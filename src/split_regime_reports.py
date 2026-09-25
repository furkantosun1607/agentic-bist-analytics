"""Measured unseen-period and regime reporting from local backtest trades."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest_reports import BacktestReportRunResult, run_backtests
from src.data import UniverseMember, load_universe, read_price_cache
from src.fundamentals_status import DEFAULT_FUNDAMENTALS_INPUT_PATH
from src.settings import Settings, load_settings
from src.splits import (
    apply_split_and_regime_labels,
    summarize_unseen_stability,
)


REGIME_COUNT_COLUMNS = ("period_split", "market_regime", "trade_count", "average_return")


@dataclass(frozen=True)
class SplitRegimeRunResult:
    status: str
    unseen_start_date: str | None
    labeled_trades: pd.DataFrame
    stability_summary: pd.DataFrame
    regime_summary: pd.DataFrame
    warnings: tuple[str, ...]
    backtest_result: BacktestReportRunResult
    output_path: Path


def run_split_regime_from_settings(
    settings: Settings | None = None,
    fundamentals_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
) -> SplitRegimeRunResult:
    """Run P36 split/regime report from configured local artifacts."""

    active_settings = settings or load_settings()
    universe = load_universe(active_settings.paths.universe)
    return run_split_regime(
        universe=universe,
        cache_dir=active_settings.paths.cache_dir,
        reports_dir=active_settings.paths.reports_dir,
        benchmark_symbol=active_settings.market_data.benchmark_symbol,
        fundamentals_path=fundamentals_path,
        unseen_start_date=active_settings.experiment.unseen_start_date,
        horizons=tuple(active_settings.backtest.horizons),
        trading_cost_bps=float(active_settings.backtest.trading_cost_bps),
        slippage_bps=float(active_settings.backtest.slippage_bps),
        regime_lookback_days=int(active_settings.experiment.regime_lookback_days),
        warn_on_small_sample_below=int(active_settings.validation.warn_on_small_sample_below),
        entry_timing=active_settings.backtest.entry_timing,
        exit_timing=active_settings.backtest.exit_timing,
    )


def run_split_regime(
    universe: list[UniverseMember],
    cache_dir: str | Path,
    reports_dir: str | Path,
    benchmark_symbol: str,
    fundamentals_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
    unseen_start_date: str | None = None,
    horizons: tuple[int, ...] = (1, 3, 5, 10, 20),
    trading_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
    regime_lookback_days: int = 20,
    warn_on_small_sample_below: int = 20,
    entry_timing: str = "next_trading_day_open",
    exit_timing: str = "close_after_horizon",
) -> SplitRegimeRunResult:
    """Run backtest, label selection/unseen and benchmark regimes, then report."""

    report_path = Path(reports_dir)
    backtest_result = run_backtests(
        universe=universe,
        cache_dir=cache_dir,
        reports_dir=reports_dir,
        benchmark_symbol=benchmark_symbol,
        fundamentals_path=fundamentals_path,
        horizons=horizons,
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
        regime_lookback_days=regime_lookback_days,
        entry_timing=entry_timing,
        exit_timing=exit_timing,
    )
    benchmark_prices = _read_optional_price_cache(cache_dir, benchmark_symbol)
    labeled_trades, label_warnings = label_backtest_trades_for_split_regime(
        trades=backtest_result.backtest.trades,
        unseen_start_date=unseen_start_date,
        benchmark_prices=benchmark_prices,
        regime_lookback_days=regime_lookback_days,
    )
    stability_summary = summarize_unseen_stability(
        labeled_trades,
        group_columns=["source", "horizon"],
        return_column="cost_adjusted_return",
    )
    regime_summary = summarize_regime_counts(labeled_trades)
    warnings = (
        *label_warnings,
        *_small_sample_warnings(stability_summary, warn_on_small_sample_below),
        *_regime_sample_warnings(regime_summary, warn_on_small_sample_below),
    )
    status = _run_status(
        unseen_start_date=unseen_start_date,
        labeled_trades=labeled_trades,
        stability_summary=stability_summary,
    )
    output_path = write_measured_split_regime_report(
        output_path=report_path / "split_regime.md",
        status=status,
        unseen_start_date=unseen_start_date,
        benchmark_symbol=benchmark_symbol,
        regime_lookback_days=regime_lookback_days,
        labeled_trades=labeled_trades,
        stability_summary=stability_summary,
        regime_summary=regime_summary,
        warnings=warnings,
    )
    return SplitRegimeRunResult(
        status=status,
        unseen_start_date=unseen_start_date,
        labeled_trades=labeled_trades,
        stability_summary=stability_summary,
        regime_summary=regime_summary,
        warnings=tuple(warnings),
        backtest_result=backtest_result,
        output_path=output_path,
    )


def label_backtest_trades_for_split_regime(
    trades: pd.DataFrame,
    unseen_start_date: str | None,
    benchmark_prices: pd.DataFrame | None,
    regime_lookback_days: int = 20,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Add decision-date split and benchmark regime labels to eligible trades."""

    if trades is None or trades.empty:
        return pd.DataFrame(), ("no backtest trades available for split/regime labeling",)

    frame = trades[trades["status"] == "ok"].copy()
    if frame.empty:
        return pd.DataFrame(), ("no tradable backtest rows available for split/regime labeling",)

    frame["signal_date"] = pd.to_datetime(
        frame["known_at"],
        errors="raise",
        utc=True,
    ).dt.date.astype(str)
    benchmark_for_merge = _benchmark_for_signal_date(benchmark_prices)
    labeled = apply_split_and_regime_labels(
        frame=frame,
        unseen_start_date=unseen_start_date,
        benchmark_prices=benchmark_for_merge,
        date_column="signal_date",
        price_column="entry_price",
        lookback_days=regime_lookback_days,
    )
    labeled["signal_date"] = pd.to_datetime(labeled["signal_date"], errors="raise").dt.date.astype(
        str
    )
    warnings: list[str] = []
    if unseen_start_date is None:
        warnings.append("experiment.unseen_start_date is not configured")
    if benchmark_prices is None:
        warnings.append("benchmark price cache missing; regime labels use trade entry prices")
    return labeled, tuple(warnings)


def summarize_regime_counts(labeled_trades: pd.DataFrame) -> pd.DataFrame:
    """Summarize observed trade counts and returns by split and market regime."""

    if labeled_trades is None or labeled_trades.empty:
        return pd.DataFrame(columns=list(REGIME_COUNT_COLUMNS))

    frame = labeled_trades.copy()
    frame["cost_adjusted_return"] = pd.to_numeric(
        frame["cost_adjusted_return"],
        errors="coerce",
    )
    summary = (
        frame.groupby(["period_split", "market_regime"], dropna=False)
        .agg(
            trade_count=("signal_id", "count"),
            average_return=("cost_adjusted_return", "mean"),
        )
        .reset_index()
        .sort_values(["period_split", "market_regime"])
    )
    return summary.loc[:, list(REGIME_COUNT_COLUMNS)]


def write_measured_split_regime_report(
    output_path: str | Path,
    status: str,
    unseen_start_date: str | None,
    benchmark_symbol: str,
    regime_lookback_days: int,
    labeled_trades: pd.DataFrame,
    stability_summary: pd.DataFrame,
    regime_summary: pd.DataFrame,
    warnings: tuple[str, ...],
) -> Path:
    """Write the measured P36 split/regime report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Unseen Period And Regime Split Report",
        "",
        f"Status: {status}.",
        f"Unseen start date: `{unseen_start_date or 'not configured'}`.",
        f"Regime benchmark: `{benchmark_symbol}` with {regime_lookback_days}-trading-day lookback.",
        "Split policy: `known_at` decision dates before the unseen start are selection rows; later dates are unseen rows.",
        "",
    ]

    if labeled_trades.empty:
        lines.extend(["No tradable backtest rows were available.", ""])
    else:
        lines.extend(
            [
                f"Trade rows: {len(labeled_trades)}.",
                f"Signal date period: {labeled_trades['signal_date'].min()} to {labeled_trades['signal_date'].max()}.",
                "",
                "## Split Counts",
                "",
                labeled_trades["period_split"].value_counts().to_markdown(),
                "",
                "## Regime Counts",
                "",
                regime_summary.to_markdown(index=False)
                if not regime_summary.empty
                else "No regime summary generated.",
                "",
            ]
        )

    if stability_summary.empty:
        lines.extend(["## Stability Summary", "", "No selection/unseen stability summary generated.", ""])
    else:
        lines.extend(["## Stability Summary", "", stability_summary.to_markdown(index=False), ""])

    if warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")

    lines.extend(
        [
            "Limitations:",
            "- This report is historical research output, not investment advice.",
            "- Selection/unseen stability is measured on fixed P35 trade-level signals, not on optimized portfolio rules.",
            "- Regime labels depend on local benchmark cache availability and the configured lookback.",
            "- Strategy variant comparison remains a separate later phase.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _run_status(
    unseen_start_date: str | None,
    labeled_trades: pd.DataFrame,
    stability_summary: pd.DataFrame,
) -> str:
    if unseen_start_date is None:
        return "inconclusive"
    if labeled_trades.empty or stability_summary.empty:
        return "inconclusive"
    if not {"selection", "unseen"}.issubset(set(labeled_trades["period_split"])):
        return "inconclusive"
    return "measured"


def _small_sample_warnings(summary: pd.DataFrame, threshold: int) -> tuple[str, ...]:
    if summary.empty or threshold <= 0:
        return ()

    warnings = []
    for _, row in summary.iterrows():
        selection_count = int(row["selection_count"])
        unseen_count = int(row["unseen_count"])
        if selection_count < threshold or unseen_count < threshold:
            warnings.append(
                "small stability sample for "
                f"{row['source']} horizon {row['horizon']}: "
                f"selection={selection_count}, unseen={unseen_count}, threshold={threshold}"
            )
    return tuple(warnings)


def _regime_sample_warnings(summary: pd.DataFrame, threshold: int) -> tuple[str, ...]:
    if summary.empty or threshold <= 0:
        return ()

    small = summary[pd.to_numeric(summary["trade_count"], errors="coerce") < threshold]
    return tuple(
        "small regime sample for "
        f"{row['period_split']}/{row['market_regime']}: "
        f"trade_count={int(row['trade_count'])}, threshold={threshold}"
        for _, row in small.iterrows()
    )


def _read_optional_price_cache(cache_dir: str | Path, symbol: str) -> pd.DataFrame | None:
    try:
        return read_price_cache(cache_dir, symbol)
    except Exception:
        return None


def _benchmark_for_signal_date(benchmark_prices: pd.DataFrame | None) -> pd.DataFrame | None:
    if benchmark_prices is None:
        return None
    frame = benchmark_prices.copy()
    if "date" in frame.columns and "signal_date" not in frame.columns:
        frame = frame.rename(columns={"date": "signal_date"})
    return frame
