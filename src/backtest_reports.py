"""Generate measured backtest and risk reporting from local research signals."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest import BacktestResult, run_backtest, write_backtest_report
from src.data import UniverseMember, load_universe, read_price_cache
from src.fundamentals import load_fundamentals_csv
from src.fundamentals_status import DEFAULT_FUNDAMENTALS_INPUT_PATH
from src.research import (
    empty_quarterly_fundamentals_frame,
    empty_sector_catch_up_frame,
    empty_technical_reversal_frame,
    empty_weekday_pattern_frame,
    run_quarterly_fundamentals,
    run_sector_catch_up,
    run_technical_reversals,
    run_weekday_patterns,
)
from src.research_reports import build_events_from_prices, load_cached_universe_prices
from src.settings import Settings, load_settings


SIGNAL_COLUMNS = ("signal_id", "symbol", "known_at", "direction", "horizon", "source")


@dataclass(frozen=True)
class BacktestReportError:
    scope: str
    message: str


@dataclass(frozen=True)
class BacktestReportRunResult:
    signals: pd.DataFrame
    backtest: BacktestResult
    missing_price_symbols: tuple[str, ...]
    errors: tuple[BacktestReportError, ...]
    output_path: Path

    @property
    def status(self) -> str:
        if self.signals.empty:
            return "no_trades"
        if self.backtest.summary.empty:
            return "inconclusive"
        ok_trades = self.backtest.trades[self.backtest.trades["status"] == "ok"]
        return "measured" if not ok_trades.empty else "no_trades"


def run_backtests_from_settings(
    settings: Settings | None = None,
    fundamentals_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
) -> BacktestReportRunResult:
    """Run the measured P35 backtest workflow from configured local artifacts."""

    active_settings = settings or load_settings()
    universe = load_universe(active_settings.paths.universe)
    return run_backtests(
        universe=universe,
        cache_dir=active_settings.paths.cache_dir,
        reports_dir=active_settings.paths.reports_dir,
        benchmark_symbol=active_settings.market_data.benchmark_symbol,
        fundamentals_path=fundamentals_path,
        horizons=tuple(active_settings.backtest.horizons),
        trading_cost_bps=float(active_settings.backtest.trading_cost_bps),
        slippage_bps=float(active_settings.backtest.slippage_bps),
        regime_lookback_days=int(active_settings.experiment.regime_lookback_days),
        entry_timing=active_settings.backtest.entry_timing,
        exit_timing=active_settings.backtest.exit_timing,
    )


def run_backtests(
    universe: list[UniverseMember],
    cache_dir: str | Path,
    reports_dir: str | Path,
    benchmark_symbol: str,
    fundamentals_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
    horizons: tuple[int, ...] = (1, 3, 5, 10, 20),
    trading_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
    regime_lookback_days: int = 20,
    entry_timing: str = "next_trading_day_open",
    exit_timing: str = "close_after_horizon",
) -> BacktestReportRunResult:
    """Assemble fixed research signals, run backtest and write risk report."""

    report_path = Path(reports_dir)
    prices_by_symbol, missing_symbols = load_cached_universe_prices(universe, cache_dir)
    benchmark_prices = _read_optional_price_cache(cache_dir, benchmark_symbol)
    symbol_to_sector = {member.yahoo_symbol: member.sector for member in universe}
    preferred_horizon = _preferred_horizon(horizons, preferred=5)
    fundamentals_horizon = _preferred_horizon(horizons, preferred=20)
    errors: list[BacktestReportError] = []

    sector_observations = empty_sector_catch_up_frame()
    try:
        sector_result = run_sector_catch_up(
            prices_by_symbol=prices_by_symbol,
            universe=universe,
            lookback_days=20,
            horizons=tuple(horizon for horizon in (5, 10, 20) if horizon in horizons) or (5,),
        )
        sector_observations = sector_result.observations
        errors.extend(
            BacktestReportError(scope=f"sector:{error.scope}", message=error.message)
            for error in sector_result.errors
        )
    except Exception as exc:
        errors.append(BacktestReportError(scope="sector_catch_up", message=str(exc)))

    weekday_observations = empty_weekday_pattern_frame()
    try:
        weekday_result = run_weekday_patterns(
            prices_by_symbol=prices_by_symbol,
            benchmark_prices=benchmark_prices,
            holding_days=tuple(horizon for horizon in (1, 2, 3, 4, 5) if horizon in horizons)
            or (1,),
            trading_cost_bps=trading_cost_bps,
            slippage_bps=slippage_bps,
            regime_lookback_days=regime_lookback_days,
        )
        weekday_observations = weekday_result.observations
        errors.extend(
            BacktestReportError(scope=f"weekday:{error.scope}", message=error.message)
            for error in weekday_result.errors
        )
    except Exception as exc:
        errors.append(BacktestReportError(scope="weekday_patterns", message=str(exc)))

    technical_observations = empty_technical_reversal_frame()
    try:
        events_by_symbol, event_errors = build_events_from_prices(prices_by_symbol)
        technical_result = run_technical_reversals(
            prices_by_symbol=prices_by_symbol,
            events_by_symbol=events_by_symbol,
            benchmark_prices=benchmark_prices,
            horizons=tuple(horizon for horizon in (1, 3, 5, 10) if horizon in horizons) or (5,),
            regime_lookback_days=regime_lookback_days,
        )
        technical_observations = technical_result.observations
        errors.extend(
            BacktestReportError(scope=f"events:{symbol}", message=message)
            for symbol, message in event_errors
        )
        errors.extend(
            BacktestReportError(scope=f"technical:{error.scope}", message=error.message)
            for error in technical_result.errors
        )
    except Exception as exc:
        errors.append(BacktestReportError(scope="technical_reversals", message=str(exc)))

    fundamentals_observations = empty_quarterly_fundamentals_frame()
    try:
        fundamentals = load_fundamentals_csv(fundamentals_path, universe)
        fundamentals_result = run_quarterly_fundamentals(
            fundamentals=fundamentals.records,
            prices_by_symbol=prices_by_symbol,
            benchmark_prices=benchmark_prices,
            horizons=tuple(horizon for horizon in (1, 5, 20) if horizon in horizons) or (20,),
        )
        errors.extend(
            BacktestReportError(
                scope=f"fundamentals_import:row_{error.row_number or 'file'}",
                message=error.message,
            )
            for error in fundamentals.errors
        )
        fundamentals_observations = fundamentals_result.observations
        errors.extend(
            BacktestReportError(scope=f"fundamentals:{error.scope}", message=error.message)
            for error in fundamentals_result.errors
        )
    except Exception as exc:
        errors.append(BacktestReportError(scope="quarterly_fundamentals", message=str(exc)))

    signals = assemble_backtest_signals(
        sector_observations=sector_observations,
        weekday_observations=weekday_observations,
        technical_observations=technical_observations,
        fundamentals_observations=fundamentals_observations,
        preferred_horizon=preferred_horizon,
        fundamentals_horizon=fundamentals_horizon,
    )
    if signals.empty:
        backtest_result = BacktestResult(
            trades=pd.DataFrame(),
            summary=pd.DataFrame(),
            errors=(),
        )
    else:
        backtest_result = run_backtest(
            signals=signals,
            prices_by_symbol=prices_by_symbol,
            benchmark_prices=benchmark_prices,
            symbol_to_sector=symbol_to_sector,
            default_horizon=preferred_horizon,
            entry_timing=entry_timing,
            exit_timing=exit_timing,
            trading_cost_bps=trading_cost_bps,
            slippage_bps=slippage_bps,
        )

    output_path = write_backtest_report(backtest_result, report_path / "backtest.md")
    result = BacktestReportRunResult(
        signals=signals,
        backtest=backtest_result,
        missing_price_symbols=tuple(missing_symbols),
        errors=tuple(errors),
        output_path=output_path,
    )
    _append_measured_backtest_metadata(
        path=output_path,
        result=result,
        benchmark_symbol=benchmark_symbol,
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
        preferred_horizon=preferred_horizon,
        fundamentals_horizon=fundamentals_horizon,
    )
    return result


def assemble_backtest_signals(
    sector_observations: pd.DataFrame,
    weekday_observations: pd.DataFrame,
    technical_observations: pd.DataFrame,
    fundamentals_observations: pd.DataFrame,
    preferred_horizon: int = 5,
    fundamentals_horizon: int = 20,
) -> pd.DataFrame:
    """Create deterministic long-only signals without using future-return columns."""

    frames = [
        _sector_signals(sector_observations, preferred_horizon),
        _weekday_signals(weekday_observations, preferred_horizon),
        _technical_signals(technical_observations, preferred_horizon),
        _fundamental_signals(fundamentals_observations, fundamentals_horizon),
    ]
    non_empty = [frame for frame in frames if not frame.empty]
    if not non_empty:
        return pd.DataFrame(columns=list(SIGNAL_COLUMNS))

    signals = pd.concat(non_empty, ignore_index=True)
    signals = signals.drop_duplicates("signal_id").sort_values(["known_at", "signal_id"])
    return signals.loc[:, list(SIGNAL_COLUMNS)].reset_index(drop=True)


def _sector_signals(observations: pd.DataFrame, horizon: int) -> pd.DataFrame:
    required = {"symbol", "date", "horizon", "status", "is_laggard"}
    if observations.empty or not required.issubset(observations.columns):
        return pd.DataFrame(columns=list(SIGNAL_COLUMNS))

    frame = observations.copy()
    selected = frame[
        (frame["status"] == "ok")
        & (pd.to_numeric(frame["horizon"], errors="coerce") == horizon)
        & (frame["is_laggard"].astype(bool))
    ].copy()
    if selected.empty:
        return pd.DataFrame(columns=list(SIGNAL_COLUMNS))

    selected["known_at"] = selected["date"].map(_after_close_timestamp)
    selected["signal_id"] = (
        "sector_catch_up:"
        + selected["symbol"].astype(str)
        + ":"
        + selected["date"].astype(str)
        + ":h"
        + selected["horizon"].astype(str)
    )
    selected["direction"] = "long"
    selected["source"] = "sector_catch_up_laggard"
    return selected.loc[:, list(SIGNAL_COLUMNS)]


def _weekday_signals(observations: pd.DataFrame, horizon: int) -> pd.DataFrame:
    required = {"symbol", "date", "holding_days", "pattern_name", "status"}
    if observations.empty or not required.issubset(observations.columns):
        return pd.DataFrame(columns=list(SIGNAL_COLUMNS))

    target_pattern = "Monday" if horizon == 1 else f"Monday_{horizon}d_hold"
    frame = observations.copy()
    selected = frame[
        (frame["status"] == "ok")
        & (pd.to_numeric(frame["holding_days"], errors="coerce") == horizon)
        & (frame["pattern_name"].astype(str) == target_pattern)
    ].copy()
    if selected.empty:
        return pd.DataFrame(columns=list(SIGNAL_COLUMNS))

    selected["known_at"] = selected["date"].map(_after_close_timestamp)
    selected["horizon"] = pd.to_numeric(selected["holding_days"], errors="coerce").astype(int)
    selected["signal_id"] = (
        "weekday_monday:"
        + selected["symbol"].astype(str)
        + ":"
        + selected["date"].astype(str)
        + ":h"
        + selected["horizon"].astype(str)
    )
    selected["direction"] = "long"
    selected["source"] = "weekday_monday_fixed"
    return selected.loc[:, list(SIGNAL_COLUMNS)]


def _technical_signals(observations: pd.DataFrame, horizon: int) -> pd.DataFrame:
    required = {
        "symbol",
        "known_at",
        "event_date",
        "event_family",
        "event_type",
        "signal_group",
        "horizon",
        "status",
    }
    if observations.empty or not required.issubset(observations.columns):
        return pd.DataFrame(columns=list(SIGNAL_COLUMNS))

    frame = observations.copy()
    selected = frame[
        (frame["status"] == "ok")
        & (pd.to_numeric(frame["horizon"], errors="coerce") == horizon)
    ].copy()
    if selected.empty:
        return pd.DataFrame(columns=list(SIGNAL_COLUMNS))

    combined = selected[selected["signal_group"].astype(str) == "combined"].copy()
    if not combined.empty:
        selected = combined

    selected["signal_id"] = (
        "technical_reversal:"
        + selected["symbol"].astype(str)
        + ":"
        + selected["event_date"].astype(str)
        + ":"
        + selected["signal_group"].astype(str)
        + ":"
        + selected["event_family"].astype(str)
        + ":"
        + selected["event_type"].astype(str)
        + ":h"
        + selected["horizon"].astype(str)
    )
    selected["direction"] = "long"
    selected["source"] = "technical_reversal_fixed"
    return selected.loc[:, list(SIGNAL_COLUMNS)]


def _fundamental_signals(observations: pd.DataFrame, horizon: int) -> pd.DataFrame:
    required = {
        "symbol",
        "disclosure_timestamp",
        "metric_name",
        "period_end",
        "horizon",
        "status",
        "qoq_change",
        "yoy_change",
    }
    if observations.empty or not required.issubset(observations.columns):
        return pd.DataFrame(columns=list(SIGNAL_COLUMNS))

    frame = observations.copy()
    qoq = pd.to_numeric(frame["qoq_change"], errors="coerce")
    yoy = pd.to_numeric(frame["yoy_change"], errors="coerce")
    selected = frame[
        (frame["status"] == "ok")
        & (pd.to_numeric(frame["horizon"], errors="coerce") == horizon)
        & ((qoq > 0) | (yoy > 0))
    ].copy()
    if selected.empty:
        return pd.DataFrame(columns=list(SIGNAL_COLUMNS))

    selected["known_at"] = selected["disclosure_timestamp"].astype(str)
    selected["signal_id"] = (
        "fundamentals_positive_change:"
        + selected["symbol"].astype(str)
        + ":"
        + selected["period_end"].astype(str)
        + ":"
        + selected["metric_name"].astype(str)
        + ":h"
        + selected["horizon"].astype(str)
    )
    selected["direction"] = "long"
    selected["source"] = "fundamentals_positive_change"
    return selected.loc[:, list(SIGNAL_COLUMNS)]


def _append_measured_backtest_metadata(
    path: Path,
    result: BacktestReportRunResult,
    benchmark_symbol: str,
    trading_cost_bps: float,
    slippage_bps: float,
    preferred_horizon: int,
    fundamentals_horizon: int,
) -> None:
    lines = [
        "",
        "## Measured Backtest Run",
        "",
        f"Status: {result.status}.",
        "Signal policy: fixed long-only signals assembled from P34 research observations without selecting on future returns.",
        f"Benchmark: `{benchmark_symbol}` local price cache.",
        f"Costs: {trading_cost_bps} bps trading cost plus {slippage_bps} bps slippage.",
        f"Primary signal horizon: {preferred_horizon} trading days.",
        f"Fundamentals signal horizon: {fundamentals_horizon} trading days.",
        "",
    ]
    if result.signals.empty:
        lines.extend(["No signals were assembled.", ""])
    else:
        lines.extend(
            [
                "## Signal Counts",
                "",
                result.signals["source"].value_counts().to_markdown(),
                "",
            ]
        )

    if result.missing_price_symbols:
        lines.extend(["## Missing Price Histories", ""])
        lines.extend(f"- `{symbol}`" for symbol in result.missing_price_symbols)
        lines.append("")

    if result.errors:
        lines.extend(["## Research Assembly Warnings", ""])
        for error in result.errors:
            lines.append(f"- `{error.scope}`: {error.message}")
        lines.append("")

    lines.extend(
        [
            "Backtest limitations:",
            "- Signals are educational research candidates, not recommendations.",
            "- Overlapping trades are summarized trade-by-trade; this is not a capital-constrained portfolio simulation.",
            "- Strategy selection, unseen-period validation and A-E strategy comparison are handled in later phases.",
            "",
        ]
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def _read_optional_price_cache(cache_dir: str | Path, symbol: str) -> pd.DataFrame | None:
    try:
        return read_price_cache(cache_dir, symbol)
    except Exception:
        return None


def _preferred_horizon(horizons: tuple[int, ...], preferred: int) -> int:
    if preferred in horizons:
        return preferred
    if not horizons:
        return preferred
    return int(horizons[0])


def _after_close_timestamp(value: object) -> str:
    date = pd.to_datetime(value, errors="raise").date().isoformat()
    return f"{date}T18:10:00+03:00"
