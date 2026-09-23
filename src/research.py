"""Research scenario orchestration for the four required analyses."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data import UniverseMember


SECTOR_CATCH_UP_COLUMNS = (
    "symbol",
    "ticker",
    "sector",
    "date",
    "peer_count",
    "status",
    "lookback_return",
    "peer_median_lookback_return",
    "catch_up_score",
    "rank_in_sector",
    "is_laggard",
    "horizon",
    "future_return",
    "peer_median_future_return",
    "future_relative_return",
    "false_positive",
)
WEEKDAY_PATTERN_COLUMNS = (
    "symbol",
    "date",
    "weekday",
    "pattern_type",
    "pattern_name",
    "holding_days",
    "status",
    "entry_close",
    "exit_close",
    "gross_return",
    "cost_bps",
    "slippage_bps",
    "cost_adjusted_return",
    "unconditional_mean_return",
    "market_regime",
    "period_split",
)
WEEKDAY_PATTERN_SUMMARY_COLUMNS = (
    "pattern_type",
    "pattern_name",
    "holding_days",
    "market_regime",
    "period_split",
    "occurrence_count",
    "average_return",
    "median_return",
    "average_cost_adjusted_return",
    "median_cost_adjusted_return",
    "unconditional_mean_return",
)
TECHNICAL_REVERSAL_COLUMNS = (
    "symbol",
    "event_family",
    "event_type",
    "event_date",
    "known_at",
    "signal_group",
    "horizon",
    "status",
    "entry_date",
    "entry_close",
    "exit_date",
    "exit_close",
    "forward_return",
    "bounce",
    "market_regime",
)
TECHNICAL_REVERSAL_SUMMARY_COLUMNS = (
    "signal_group",
    "event_family",
    "event_type",
    "horizon",
    "market_regime",
    "event_count",
    "bounce_count",
    "failure_count",
    "bounce_rate",
    "average_return",
    "median_return",
)


@dataclass(frozen=True)
class ResearchError:
    scope: str
    message: str


@dataclass(frozen=True)
class SectorCatchUpResult:
    observations: pd.DataFrame
    errors: tuple[ResearchError, ...]


@dataclass(frozen=True)
class WeekdayPatternResult:
    observations: pd.DataFrame
    summary: pd.DataFrame
    errors: tuple[ResearchError, ...]


@dataclass(frozen=True)
class TechnicalReversalResult:
    observations: pd.DataFrame
    summary: pd.DataFrame
    errors: tuple[ResearchError, ...]


class ResearchInputError(ValueError):
    """Raised when research inputs are structurally invalid."""


def run_sector_catch_up(
    prices_by_symbol: dict[str, pd.DataFrame],
    universe: list[UniverseMember],
    lookback_days: int = 20,
    horizons: tuple[int, ...] = (5, 10, 20),
) -> SectorCatchUpResult:
    """Run the sector catch-up scenario on normalized price histories."""

    _validate_sector_catch_up_args(lookback_days, horizons)
    errors: list[ResearchError] = []

    try:
        price_panel = _build_sector_price_panel(prices_by_symbol, universe)
    except Exception as exc:
        return SectorCatchUpResult(
            observations=empty_sector_catch_up_frame(),
            errors=(ResearchError(scope="sector_catch_up", message=str(exc)),),
        )

    if price_panel.empty:
        return SectorCatchUpResult(
            observations=empty_sector_catch_up_frame(),
            errors=(ResearchError(scope="sector_catch_up", message="price panel is empty"),),
        )

    observations: list[pd.DataFrame] = []
    panel = price_panel.sort_values(["symbol", "date"]).copy()
    panel["lookback_return"] = panel.groupby("symbol")["close"].pct_change(lookback_days)

    for horizon in horizons:
        try:
            horizon_frame = _sector_catch_up_for_horizon(panel, horizon)
        except Exception as exc:
            errors.append(ResearchError(scope=f"horizon_{horizon}", message=str(exc)))
            continue

        observations.append(horizon_frame)

    if not observations:
        return SectorCatchUpResult(
            observations=empty_sector_catch_up_frame(),
            errors=tuple(errors)
            or (ResearchError(scope="sector_catch_up", message="no horizons were evaluated"),),
        )

    combined = pd.concat(observations, ignore_index=True)
    return SectorCatchUpResult(
        observations=combined.loc[:, list(SECTOR_CATCH_UP_COLUMNS)],
        errors=tuple(errors),
    )


def write_sector_catch_up_report(
    result: SectorCatchUpResult,
    output_path: str | Path,
    lookback_days: int = 20,
) -> Path:
    """Write a compact markdown report for sector catch-up results."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    observations = result.observations

    lines = [
        "# Sector Catch-Up Report",
        "",
        f"Lookback window: {lookback_days} trading days.",
        "Signals: laggards are rows where stock lookback return is below eligible peer median.",
        "Peer rule: same simplified sector, excluding the stock itself.",
        "",
    ]

    if observations.empty:
        lines.extend(
            [
                "Status: no observations generated.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"Data period: {observations['date'].min()} to {observations['date'].max()}.",
                f"Observation rows: {len(observations)}.",
                f"Symbols: {observations['symbol'].nunique()}.",
                "",
                "## Status Counts",
                "",
                observations["status"].value_counts().to_markdown(),
                "",
                "## Laggard Outcomes",
                "",
                _laggard_summary_markdown(observations),
                "",
            ]
        )

    if result.errors:
        lines.extend(["## Errors", ""])
        for error in result.errors:
            lines.append(f"- `{error.scope}`: {error.message}")
        lines.append("")

    lines.extend(
        [
            "Limitations:",
            "- This report is historical research output, not investment advice.",
            "- Results depend on cached price histories and fixed universe sector labels.",
            "- Fundamental, macro, news and video context are added in later phases.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_weekday_patterns(
    prices_by_symbol: dict[str, pd.DataFrame],
    benchmark_prices: pd.DataFrame | None = None,
    holding_days: tuple[int, ...] = (1, 2, 3, 4, 5),
    trading_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
    regime_lookback_days: int = 20,
    unseen_start_date: str | None = None,
) -> WeekdayPatternResult:
    """Run weekday and two-to-five-day calendar pattern tests."""

    _validate_weekday_pattern_args(holding_days, trading_cost_bps, slippage_bps)
    errors: list[ResearchError] = []
    observations: list[pd.DataFrame] = []

    benchmark_panel = None
    if benchmark_prices is not None:
        try:
            benchmark_panel = _prepare_benchmark_regime(benchmark_prices, regime_lookback_days)
        except Exception as exc:
            errors.append(ResearchError(scope="benchmark_regime", message=str(exc)))

    for symbol, prices in prices_by_symbol.items():
        try:
            symbol_frame = _weekday_patterns_for_symbol(
                prices=prices,
                symbol=symbol,
                benchmark_panel=benchmark_panel,
                holding_days=holding_days,
                trading_cost_bps=trading_cost_bps,
                slippage_bps=slippage_bps,
                regime_lookback_days=regime_lookback_days,
                unseen_start_date=unseen_start_date,
            )
        except Exception as exc:
            errors.append(ResearchError(scope=symbol, message=str(exc)))
            continue

        observations.append(symbol_frame)

    if not observations:
        return WeekdayPatternResult(
            observations=empty_weekday_pattern_frame(),
            summary=empty_weekday_pattern_summary_frame(),
            errors=tuple(errors)
            or (ResearchError(scope="weekday_patterns", message="no symbols were evaluated"),),
        )

    combined = pd.concat(observations, ignore_index=True)
    summary = summarize_weekday_patterns(combined)
    return WeekdayPatternResult(
        observations=combined.loc[:, list(WEEKDAY_PATTERN_COLUMNS)],
        summary=summary,
        errors=tuple(errors),
    )


def summarize_weekday_patterns(observations: pd.DataFrame) -> pd.DataFrame:
    """Summarize eligible weekday pattern observations."""

    if observations.empty:
        return empty_weekday_pattern_summary_frame()

    eligible = observations[observations["status"] == "ok"].copy()
    if eligible.empty:
        return empty_weekday_pattern_summary_frame()

    summary = (
        eligible.groupby(
            [
                "pattern_type",
                "pattern_name",
                "holding_days",
                "market_regime",
                "period_split",
            ],
            dropna=False,
        )
        .agg(
            occurrence_count=("symbol", "count"),
            average_return=("gross_return", "mean"),
            median_return=("gross_return", "median"),
            average_cost_adjusted_return=("cost_adjusted_return", "mean"),
            median_cost_adjusted_return=("cost_adjusted_return", "median"),
            unconditional_mean_return=("unconditional_mean_return", "mean"),
        )
        .reset_index()
    )
    return summary.loc[:, list(WEEKDAY_PATTERN_SUMMARY_COLUMNS)]


def write_weekday_patterns_report(
    result: WeekdayPatternResult,
    output_path: str | Path,
) -> Path:
    """Write a compact markdown report for weekday pattern results."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Weekday And Multi-Day Pattern Report",
        "",
        "Patterns: weekday entry tests and two-to-five-trading-day holding tests.",
        "Costs: reported with configured trading cost and slippage deducted from gross returns.",
        "Multiple-testing note: calendar effects are exploratory and must be treated as fragile until unseen-period stability is checked.",
        "",
    ]

    if result.observations.empty:
        lines.extend(["Status: no observations generated.", ""])
    else:
        lines.extend(
            [
                f"Data period: {result.observations['date'].min()} to {result.observations['date'].max()}.",
                f"Observation rows: {len(result.observations)}.",
                f"Symbols: {result.observations['symbol'].nunique()}.",
                "",
                "## Status Counts",
                "",
                result.observations["status"].value_counts().to_markdown(),
                "",
            ]
        )

    if result.summary.empty:
        lines.extend(["## Summary", "", "No eligible pattern observations.", ""])
    else:
        lines.extend(["## Summary", "", result.summary.to_markdown(index=False), ""])

    if result.errors:
        lines.extend(["## Errors", ""])
        for error in result.errors:
            lines.append(f"- `{error.scope}`: {error.message}")
        lines.append("")

    lines.extend(
        [
            "Limitations:",
            "- This report is historical research output, not investment advice.",
            "- Calendar effects are vulnerable to multiple testing and regime instability.",
            "- Fundamental, macro, news and video context are added in later phases.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_technical_reversals(
    prices_by_symbol: dict[str, pd.DataFrame],
    events_by_symbol: dict[str, pd.DataFrame],
    benchmark_prices: pd.DataFrame | None = None,
    horizons: tuple[int, ...] = (1, 3, 5, 10),
    regime_lookback_days: int = 20,
) -> TechnicalReversalResult:
    """Compare technical events with future returns."""

    _validate_reversal_args(horizons)
    errors: list[ResearchError] = []
    observations: list[pd.DataFrame] = []

    benchmark_panel = None
    if benchmark_prices is not None:
        try:
            benchmark_panel = _prepare_benchmark_regime(benchmark_prices, regime_lookback_days)
        except Exception as exc:
            errors.append(ResearchError(scope="benchmark_regime", message=str(exc)))

    for symbol, events in events_by_symbol.items():
        try:
            prices = prices_by_symbol.get(symbol)
            if prices is None:
                raise ResearchInputError(f"missing price history for {symbol}")

            symbol_observations = _technical_reversals_for_symbol(
                prices=prices,
                events=events,
                symbol=symbol,
                benchmark_panel=benchmark_panel,
                horizons=horizons,
                regime_lookback_days=regime_lookback_days,
            )
        except Exception as exc:
            errors.append(ResearchError(scope=symbol, message=str(exc)))
            continue

        observations.append(symbol_observations)

    if not observations:
        return TechnicalReversalResult(
            observations=empty_technical_reversal_frame(),
            summary=empty_technical_reversal_summary_frame(),
            errors=tuple(errors)
            or (ResearchError(scope="technical_reversals", message="no events were evaluated"),),
        )

    combined = pd.concat(observations, ignore_index=True)
    summary = summarize_technical_reversals(combined)
    return TechnicalReversalResult(
        observations=combined.loc[:, list(TECHNICAL_REVERSAL_COLUMNS)],
        summary=summary,
        errors=tuple(errors),
    )


def summarize_technical_reversals(observations: pd.DataFrame) -> pd.DataFrame:
    """Summarize eligible technical reversal outcomes."""

    if observations.empty:
        return empty_technical_reversal_summary_frame()

    eligible = observations[observations["status"] == "ok"].copy()
    if eligible.empty:
        return empty_technical_reversal_summary_frame()

    summary = (
        eligible.groupby(
            [
                "signal_group",
                "event_family",
                "event_type",
                "horizon",
                "market_regime",
            ],
            dropna=False,
        )
        .agg(
            event_count=("symbol", "count"),
            bounce_count=("bounce", "sum"),
            average_return=("forward_return", "mean"),
            median_return=("forward_return", "median"),
        )
        .reset_index()
    )
    summary["failure_count"] = summary["event_count"] - summary["bounce_count"]
    summary["bounce_rate"] = summary["bounce_count"] / summary["event_count"]
    return summary.loc[:, list(TECHNICAL_REVERSAL_SUMMARY_COLUMNS)]


def write_technical_reversals_report(
    result: TechnicalReversalResult,
    output_path: str | Path,
) -> Path:
    """Write a compact markdown report for technical reversal results."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Technical Reversal Report",
        "",
        "Events: deterministic technical event detector output from Scenario 3.",
        "Timing: each event becomes tradable no earlier than the next available trading day.",
        "Combined signals: multiple same-symbol same-date events are collapsed into a separate combined observation.",
        "",
    ]

    if result.observations.empty:
        lines.extend(["Status: no observations generated.", ""])
    else:
        lines.extend(
            [
                f"Event period: {result.observations['event_date'].min()} to {result.observations['event_date'].max()}.",
                f"Observation rows: {len(result.observations)}.",
                f"Symbols: {result.observations['symbol'].nunique()}.",
                "",
                "## Status Counts",
                "",
                result.observations["status"].value_counts().to_markdown(),
                "",
            ]
        )

    if result.summary.empty:
        lines.extend(["## Summary", "", "No eligible reversal observations.", ""])
    else:
        lines.extend(["## Summary", "", result.summary.to_markdown(index=False), ""])

    if result.errors:
        lines.extend(["## Errors", ""])
        for error in result.errors:
            lines.append(f"- `{error.scope}`: {error.message}")
        lines.append("")

    lines.extend(
        [
            "Limitations:",
            "- This report is historical research output, not investment advice.",
            "- Event definitions are intentionally simple and are not optimized.",
            "- Fundamental, macro, news and video context are added in later phases.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def empty_sector_catch_up_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(SECTOR_CATCH_UP_COLUMNS))


def empty_weekday_pattern_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(WEEKDAY_PATTERN_COLUMNS))


def empty_weekday_pattern_summary_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(WEEKDAY_PATTERN_SUMMARY_COLUMNS))


def empty_technical_reversal_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(TECHNICAL_REVERSAL_COLUMNS))


def empty_technical_reversal_summary_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(TECHNICAL_REVERSAL_SUMMARY_COLUMNS))


def _technical_reversals_for_symbol(
    prices: pd.DataFrame,
    events: pd.DataFrame,
    symbol: str,
    benchmark_panel: pd.DataFrame | None,
    horizons: tuple[int, ...],
    regime_lookback_days: int,
) -> pd.DataFrame:
    _require_columns(prices, ["date", "close"], scope=symbol)
    _require_columns(
        events,
        ["event_family", "event_type", "event_date", "known_at"],
        scope=f"{symbol} events",
    )
    price_frame = prices.loc[:, ["date", "close"]].copy()
    price_frame["date"] = pd.to_datetime(price_frame["date"], errors="raise")
    price_frame["close"] = pd.to_numeric(price_frame["close"], errors="raise")
    price_frame = price_frame.sort_values("date").reset_index(drop=True)
    if price_frame["date"].duplicated().any():
        raise ResearchInputError(f"{symbol} contains duplicate dates")

    if benchmark_panel is not None:
        price_frame = price_frame.merge(benchmark_panel, on="date", how="left")
    else:
        price_frame["regime_return"] = price_frame["close"].pct_change(regime_lookback_days)

    price_frame["market_regime"] = "unknown"
    price_frame.loc[price_frame["regime_return"] >= 0, "market_regime"] = "rising"
    price_frame.loc[price_frame["regime_return"] < 0, "market_regime"] = "falling"

    event_frame = events.copy()
    event_frame["event_date"] = pd.to_datetime(event_frame["event_date"], errors="raise")
    event_frame = event_frame.sort_values(["event_date", "event_family", "event_type"])
    individual = _technical_reversal_rows(
        price_frame=price_frame,
        event_frame=event_frame,
        symbol=symbol,
        horizons=horizons,
        signal_group="individual",
    )
    combined = _combined_reversal_rows(
        price_frame=price_frame,
        event_frame=event_frame,
        symbol=symbol,
        horizons=horizons,
    )
    frames = [individual]
    if not combined.empty:
        frames.append(combined)
    return pd.concat(frames, ignore_index=True).loc[:, list(TECHNICAL_REVERSAL_COLUMNS)]


def _technical_reversal_rows(
    price_frame: pd.DataFrame,
    event_frame: pd.DataFrame,
    symbol: str,
    horizons: tuple[int, ...],
    signal_group: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, event in event_frame.iterrows():
        for horizon in horizons:
            rows.append(
                _reversal_observation(
                    price_frame=price_frame,
                    symbol=symbol,
                    event_family=str(event["event_family"]),
                    event_type=str(event["event_type"]),
                    event_date=event["event_date"],
                    known_at=str(event["known_at"]),
                    signal_group=signal_group,
                    horizon=horizon,
                )
            )
    return pd.DataFrame(rows, columns=list(TECHNICAL_REVERSAL_COLUMNS))


def _combined_reversal_rows(
    price_frame: pd.DataFrame,
    event_frame: pd.DataFrame,
    symbol: str,
    horizons: tuple[int, ...],
) -> pd.DataFrame:
    combined_events = []
    grouped = event_frame.groupby("event_date", sort=True)
    for event_date, group in grouped:
        if len(group) < 2:
            continue
        known_at = str(group["known_at"].max())
        event_types = sorted(group["event_type"].astype(str).unique())
        combined_events.append(
            {
                "event_family": "combined",
                "event_type": "+".join(event_types),
                "event_date": event_date,
                "known_at": known_at,
            }
        )

    if not combined_events:
        return empty_technical_reversal_frame()

    return _technical_reversal_rows(
        price_frame=price_frame,
        event_frame=pd.DataFrame(combined_events),
        symbol=symbol,
        horizons=horizons,
        signal_group="combined",
    )


def _reversal_observation(
    price_frame: pd.DataFrame,
    symbol: str,
    event_family: str,
    event_type: str,
    event_date: pd.Timestamp,
    known_at: str,
    signal_group: str,
    horizon: int,
) -> dict[str, object]:
    entry_index = price_frame.index[price_frame["date"] > event_date]
    row = {
        "symbol": symbol,
        "event_family": event_family,
        "event_type": event_type,
        "event_date": event_date.date().isoformat(),
        "known_at": known_at,
        "signal_group": signal_group,
        "horizon": horizon,
        "status": "ok",
        "entry_date": pd.NA,
        "entry_close": pd.NA,
        "exit_date": pd.NA,
        "exit_close": pd.NA,
        "forward_return": pd.NA,
        "bounce": False,
        "market_regime": "unknown",
    }
    if len(entry_index) == 0:
        row["status"] = "insufficient_forward_history"
        return row

    entry_pos = int(entry_index[0])
    exit_pos = entry_pos + horizon
    if exit_pos >= len(price_frame):
        entry = price_frame.iloc[entry_pos]
        row.update(
            {
                "entry_date": entry["date"].date().isoformat(),
                "entry_close": float(entry["close"]),
                "market_regime": str(entry["market_regime"]),
                "status": "insufficient_forward_history",
            }
        )
        return row

    entry = price_frame.iloc[entry_pos]
    exit_row = price_frame.iloc[exit_pos]
    forward_return = float(exit_row["close"] / entry["close"] - 1)
    row.update(
        {
            "entry_date": entry["date"].date().isoformat(),
            "entry_close": float(entry["close"]),
            "exit_date": exit_row["date"].date().isoformat(),
            "exit_close": float(exit_row["close"]),
            "forward_return": forward_return,
            "bounce": forward_return > 0,
            "market_regime": str(entry["market_regime"]),
        }
    )
    if row["market_regime"] == "unknown":
        row["status"] = "insufficient_regime_history"
    return row


def _weekday_patterns_for_symbol(
    prices: pd.DataFrame,
    symbol: str,
    benchmark_panel: pd.DataFrame | None,
    holding_days: tuple[int, ...],
    trading_cost_bps: float,
    slippage_bps: float,
    regime_lookback_days: int,
    unseen_start_date: str | None,
) -> pd.DataFrame:
    _require_columns(prices, ["date", "close"], scope=symbol)
    frame = prices.loc[:, ["date", "close"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["close"] = pd.to_numeric(frame["close"], errors="raise")
    frame = frame.sort_values("date").reset_index(drop=True)
    if frame["date"].duplicated().any():
        raise ResearchInputError(f"{symbol} contains duplicate dates")

    if benchmark_panel is not None:
        frame = frame.merge(benchmark_panel, on="date", how="left")
    else:
        frame["regime_return"] = frame["close"].pct_change(regime_lookback_days)

    frame["market_regime"] = "unknown"
    frame.loc[frame["regime_return"] >= 0, "market_regime"] = "rising"
    frame.loc[frame["regime_return"] < 0, "market_regime"] = "falling"
    frame["period_split"] = _period_split(frame["date"], unseen_start_date)
    frame["weekday"] = frame["date"].dt.day_name()
    frame["date"] = frame["date"].dt.date.astype(str)

    total_cost = (trading_cost_bps + slippage_bps) / 10000
    outputs: list[pd.DataFrame] = []
    unconditional_by_holding: dict[int, float] = {}

    for holding in holding_days:
        exit_close = frame["close"].shift(-holding)
        gross_return = exit_close / frame["close"] - 1
        unconditional_by_holding[holding] = float(gross_return.dropna().mean())

        pattern_type = "weekday" if holding == 1 else "multi_day"
        pattern_name = (
            frame["weekday"]
            if holding == 1
            else frame["weekday"] + f"_{holding}d_hold"
        )
        status = pd.Series("ok", index=frame.index, dtype="object")
        status.loc[exit_close.isna()] = "insufficient_forward_history"
        status.loc[frame["market_regime"] == "unknown"] = "insufficient_regime_history"

        output = pd.DataFrame(
            {
                "symbol": symbol,
                "date": frame["date"],
                "weekday": frame["weekday"],
                "pattern_type": pattern_type,
                "pattern_name": pattern_name,
                "holding_days": holding,
                "status": status,
                "entry_close": frame["close"],
                "exit_close": exit_close,
                "gross_return": gross_return,
                "cost_bps": trading_cost_bps,
                "slippage_bps": slippage_bps,
                "cost_adjusted_return": gross_return - total_cost,
                "unconditional_mean_return": unconditional_by_holding[holding],
                "market_regime": frame["market_regime"],
                "period_split": frame["period_split"],
            }
        )
        outputs.append(output)

    return pd.concat(outputs, ignore_index=True).loc[:, list(WEEKDAY_PATTERN_COLUMNS)]


def _prepare_benchmark_regime(
    benchmark_prices: pd.DataFrame,
    regime_lookback_days: int,
) -> pd.DataFrame:
    _require_columns(benchmark_prices, ["date", "close"], scope="benchmark")
    benchmark = benchmark_prices.loc[:, ["date", "close"]].copy()
    benchmark["date"] = pd.to_datetime(benchmark["date"], errors="raise")
    benchmark["close"] = pd.to_numeric(benchmark["close"], errors="raise")
    benchmark = benchmark.sort_values("date").reset_index(drop=True)
    if benchmark["date"].duplicated().any():
        raise ResearchInputError("benchmark contains duplicate dates")

    benchmark["regime_return"] = benchmark["close"].pct_change(regime_lookback_days)
    return benchmark.loc[:, ["date", "regime_return"]]


def _sector_catch_up_for_horizon(panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
    frame = panel.copy()
    frame["future_return"] = frame.groupby("symbol")["close"].shift(-horizon) / frame["close"] - 1
    frame["peer_count"] = frame.groupby(["sector", "date"])["symbol"].transform("count") - 1
    frame["peer_median_lookback_return"] = _peer_median(
        frame,
        value_column="lookback_return",
    )
    frame["peer_median_future_return"] = _peer_median(
        frame,
        value_column="future_return",
    )
    frame["catch_up_score"] = (
        frame["lookback_return"] - frame["peer_median_lookback_return"]
    )
    frame["future_relative_return"] = (
        frame["future_return"] - frame["peer_median_future_return"]
    )
    frame["rank_in_sector"] = frame.groupby(["sector", "date"])["lookback_return"].rank(
        method="first",
        ascending=False,
    )
    frame["is_laggard"] = frame["catch_up_score"] < 0
    frame["horizon"] = horizon
    frame["status"] = "ok"
    frame.loc[frame["peer_count"] < 1, "status"] = "insufficient_peers"
    frame.loc[frame["lookback_return"].isna(), "status"] = "insufficient_history"
    frame.loc[frame["future_return"].isna(), "status"] = "insufficient_forward_history"
    frame.loc[
        frame["peer_median_future_return"].isna() & (frame["peer_count"] >= 1),
        "status",
    ] = "insufficient_peer_forward_history"
    frame["false_positive"] = (
        (frame["status"] == "ok")
        & frame["is_laggard"]
        & (frame["future_relative_return"] <= 0)
    )

    return frame.loc[:, list(SECTOR_CATCH_UP_COLUMNS)]


def _peer_median(frame: pd.DataFrame, value_column: str) -> pd.Series:
    peers = frame[["sector", "date", "symbol", value_column]].copy()
    merged = peers.merge(peers, on=["sector", "date"], suffixes=("", "_peer"))
    merged = merged[merged["symbol"] != merged["symbol_peer"]]
    medians = (
        merged.groupby(["symbol", "date"])[f"{value_column}_peer"]
        .median()
        .rename(f"peer_median_{value_column}")
        .reset_index()
    )
    aligned = frame[["symbol", "date"]].merge(medians, on=["symbol", "date"], how="left")
    return aligned[f"peer_median_{value_column}"]


def _build_sector_price_panel(
    prices_by_symbol: dict[str, pd.DataFrame],
    universe: list[UniverseMember],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    universe_by_symbol = {member.yahoo_symbol: member for member in universe}

    for symbol, prices in prices_by_symbol.items():
        try:
            _require_columns(prices, ["date", "close"], scope=symbol)
            member = universe_by_symbol.get(symbol)
            if member is None:
                raise ResearchInputError(f"{symbol} is not in the fixed universe")

            frame = prices.loc[:, ["date", "close"]].copy()
            frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date.astype(str)
            frame["close"] = pd.to_numeric(frame["close"], errors="raise")
            frame["symbol"] = symbol
            frame["ticker"] = member.ticker
            frame["sector"] = member.sector
            frames.append(frame)
        except Exception as exc:
            raise ResearchInputError(f"failed to prepare {symbol}: {exc}") from exc

    if not frames:
        return pd.DataFrame(columns=["symbol", "ticker", "sector", "date", "close"])

    panel = pd.concat(frames, ignore_index=True)
    return panel.loc[:, ["symbol", "ticker", "sector", "date", "close"]]


def _require_columns(frame: pd.DataFrame, columns: list[str], scope: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ResearchInputError(f"{scope} missing required columns: {', '.join(missing)}")


def _validate_sector_catch_up_args(lookback_days: int, horizons: tuple[int, ...]) -> None:
    if lookback_days <= 0:
        raise ResearchInputError("lookback_days must be positive")
    if not horizons:
        raise ResearchInputError("at least one horizon is required")
    invalid_horizons = [horizon for horizon in horizons if horizon <= 0]
    if invalid_horizons:
        raise ResearchInputError(f"horizons must be positive: {invalid_horizons}")


def _validate_weekday_pattern_args(
    holding_days: tuple[int, ...],
    trading_cost_bps: float,
    slippage_bps: float,
) -> None:
    if not holding_days:
        raise ResearchInputError("at least one holding day is required")
    invalid_holding = [holding for holding in holding_days if holding <= 0]
    if invalid_holding:
        raise ResearchInputError(f"holding_days must be positive: {invalid_holding}")
    if min(holding_days) < 1 or max(holding_days) > 5:
        raise ResearchInputError("holding_days must stay within the predefined 1-5 range")
    if trading_cost_bps < 0:
        raise ResearchInputError("trading_cost_bps cannot be negative")
    if slippage_bps < 0:
        raise ResearchInputError("slippage_bps cannot be negative")


def _validate_reversal_args(horizons: tuple[int, ...]) -> None:
    if not horizons:
        raise ResearchInputError("at least one reversal horizon is required")
    invalid_horizons = [horizon for horizon in horizons if horizon <= 0]
    if invalid_horizons:
        raise ResearchInputError(f"horizons must be positive: {invalid_horizons}")


def _period_split(dates: pd.Series, unseen_start_date: str | None) -> pd.Series:
    if unseen_start_date is None:
        return pd.Series("full_sample", index=dates.index, dtype="object")

    unseen_start = pd.to_datetime(unseen_start_date, errors="raise")
    split = pd.Series("selection", index=dates.index, dtype="object")
    split.loc[dates >= unseen_start] = "unseen"
    return split


def _laggard_summary_markdown(observations: pd.DataFrame) -> str:
    ok_laggards = observations[(observations["status"] == "ok") & observations["is_laggard"]]
    if ok_laggards.empty:
        return "No eligible laggard observations."

    summary = (
        ok_laggards.groupby("horizon")
        .agg(
            observations=("symbol", "count"),
            average_future_relative_return=("future_relative_return", "mean"),
            median_future_relative_return=("future_relative_return", "median"),
            false_positives=("false_positive", "sum"),
        )
        .reset_index()
    )
    return summary.to_markdown(index=False)
