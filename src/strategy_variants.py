"""Strategy variant comparison A-E."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest import BACKTEST_SUMMARY_COLUMNS, run_backtest


VARIANT_BACKTEST_SUMMARY_COLUMNS = tuple(
    column for column in BACKTEST_SUMMARY_COLUMNS if column != "status"
)
VARIANT_SUMMARY_COLUMNS = (
    "variant",
    "description",
    "status",
    "components",
    "missing_components",
    "data_start",
    "data_end",
    "trading_cost_bps",
    "slippage_bps",
    *VARIANT_BACKTEST_SUMMARY_COLUMNS,
)
VARIANT_TRADE_COLUMNS = ("variant", "component", "component_signal_id")


@dataclass(frozen=True)
class StrategyVariant:
    name: str
    description: str
    required_components: tuple[str, ...]


@dataclass(frozen=True)
class StrategyVariantError:
    variant: str
    message: str


@dataclass(frozen=True)
class StrategyVariantComparisonResult:
    summary: pd.DataFrame
    trades: pd.DataFrame
    errors: tuple[StrategyVariantError, ...]


class StrategyVariantInputError(ValueError):
    """Raised when strategy variant inputs are structurally invalid."""


STRATEGY_VARIANTS = (
    StrategyVariant(
        name="A",
        description="technical",
        required_components=("technical",),
    ),
    StrategyVariant(
        name="B",
        description="technical + sector",
        required_components=("technical", "sector"),
    ),
    StrategyVariant(
        name="C",
        description="technical + sector + fundamentals",
        required_components=("technical", "sector", "fundamentals"),
    ),
    StrategyVariant(
        name="D",
        description="technical + sector + fundamentals + macro",
        required_components=("technical", "sector", "fundamentals", "macro"),
    ),
    StrategyVariant(
        name="E",
        description="technical + sector + fundamentals + macro + verified news/video context",
        required_components=(
            "technical",
            "sector",
            "fundamentals",
            "macro",
            "news_video",
        ),
    ),
)


def compare_strategy_variants(
    signals_by_component: dict[str, pd.DataFrame],
    prices_by_symbol: dict[str, pd.DataFrame],
    benchmark_prices: pd.DataFrame | None = None,
    sector_benchmark_prices: dict[str, pd.DataFrame] | None = None,
    symbol_to_sector: dict[str, str] | None = None,
    default_horizon: int = 5,
    trading_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> StrategyVariantComparisonResult:
    """Compare predefined strategy variants on the same data and cost assumptions."""

    _validate_inputs(signals_by_component, prices_by_symbol)
    data_start, data_end = _price_data_period(prices_by_symbol)
    summaries: list[dict[str, object]] = []
    trade_frames: list[pd.DataFrame] = []
    errors: list[StrategyVariantError] = []

    for variant in STRATEGY_VARIANTS:
        missing = _missing_components(signals_by_component, variant.required_components)
        if missing:
            summaries.append(
                _unavailable_summary_row(
                    variant=variant,
                    missing_components=missing,
                    data_start=data_start,
                    data_end=data_end,
                    trading_cost_bps=trading_cost_bps,
                    slippage_bps=slippage_bps,
                )
            )
            continue

        try:
            signals = _combine_variant_signals(signals_by_component, variant)
            result = run_backtest(
                signals=signals,
                prices_by_symbol=prices_by_symbol,
                benchmark_prices=benchmark_prices,
                sector_benchmark_prices=sector_benchmark_prices,
                symbol_to_sector=symbol_to_sector,
                default_horizon=default_horizon,
                trading_cost_bps=trading_cost_bps,
                slippage_bps=slippage_bps,
            )
            summaries.append(
                _summary_row_from_backtest(
                    variant=variant,
                    result_summary=result.summary,
                    data_start=data_start,
                    data_end=data_end,
                    trading_cost_bps=trading_cost_bps,
                    slippage_bps=slippage_bps,
                )
            )
            if not result.trades.empty:
                trades = result.trades.copy()
                trades.insert(0, "variant", variant.name)
                trades["component"] = trades["signal_id"].map(_component_from_signal_id)
                trades["component_signal_id"] = trades["signal_id"].map(
                    _component_signal_id_from_signal_id
                )
                trade_frames.append(trades)
            errors.extend(
                StrategyVariantError(variant=variant.name, message=f"{error.scope}: {error.message}")
                for error in result.errors
            )
        except Exception as exc:
            errors.append(StrategyVariantError(variant=variant.name, message=str(exc)))
            summaries.append(
                _error_summary_row(
                    variant=variant,
                    message=str(exc),
                    data_start=data_start,
                    data_end=data_end,
                    trading_cost_bps=trading_cost_bps,
                    slippage_bps=slippage_bps,
                )
            )

    trades = (
        pd.concat(trade_frames, ignore_index=True)
        if trade_frames
        else pd.DataFrame(columns=["variant"])
    )
    return StrategyVariantComparisonResult(
        summary=pd.DataFrame(summaries).loc[:, list(VARIANT_SUMMARY_COLUMNS)],
        trades=trades,
        errors=tuple(errors),
    )


def compare_strategy_variants_from_settings(
    signals_by_component: dict[str, pd.DataFrame],
    prices_by_symbol: dict[str, pd.DataFrame],
    settings,
    benchmark_prices: pd.DataFrame | None = None,
    sector_benchmark_prices: dict[str, pd.DataFrame] | None = None,
    symbol_to_sector: dict[str, str] | None = None,
) -> StrategyVariantComparisonResult:
    """Compare strategy variants using configured horizon and cost assumptions."""

    if not settings.backtest.horizons:
        raise StrategyVariantInputError("settings.backtest.horizons must contain at least one value")

    return compare_strategy_variants(
        signals_by_component=signals_by_component,
        prices_by_symbol=prices_by_symbol,
        benchmark_prices=benchmark_prices,
        sector_benchmark_prices=sector_benchmark_prices,
        symbol_to_sector=symbol_to_sector,
        default_horizon=int(settings.backtest.horizons[0]),
        trading_cost_bps=float(settings.backtest.trading_cost_bps),
        slippage_bps=float(settings.backtest.slippage_bps),
    )


def write_strategy_variants_report(
    result: StrategyVariantComparisonResult,
    output_path: str | Path,
) -> Path:
    """Write a compact markdown report for strategy variant comparisons."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Strategy Variant Comparison A-E",
        "",
        "Variants:",
        "- A: technical",
        "- B: technical + sector",
        "- C: B + fundamentals",
        "- D: C + macro",
        "- E: D + verified news/video context",
        "",
    ]
    if result.summary.empty:
        lines.extend(["Status: no variant summary generated.", ""])
    else:
        lines.extend(["## Summary", "", result.summary.to_markdown(index=False), ""])

    if result.errors:
        lines.extend(["## Errors", ""])
        for error in result.errors:
            lines.append(f"- `{error.variant}`: {error.message}")
        lines.append("")

    lines.extend(
        [
            "Limitations:",
            "- Missing-source variants are marked unavailable; values are not invented.",
            "- All variants use the same provided price data, benchmark hooks and cost assumptions.",
            "- This report is historical research infrastructure, not investment advice.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _validate_inputs(
    signals_by_component: dict[str, pd.DataFrame],
    prices_by_symbol: dict[str, pd.DataFrame],
) -> None:
    if not isinstance(signals_by_component, dict):
        raise StrategyVariantInputError("signals_by_component must be a dict")
    if not isinstance(prices_by_symbol, dict) or not prices_by_symbol:
        raise StrategyVariantInputError("prices_by_symbol must be a non-empty dict")
    for component, signals in signals_by_component.items():
        if not isinstance(signals, pd.DataFrame):
            raise StrategyVariantInputError(f"{component} signals must be a DataFrame")


def _missing_components(
    signals_by_component: dict[str, pd.DataFrame],
    required_components: tuple[str, ...],
) -> tuple[str, ...]:
    missing = []
    for component in required_components:
        signals = signals_by_component.get(component)
        if signals is None or signals.empty:
            missing.append(component)
    return tuple(missing)


def _combine_variant_signals(
    signals_by_component: dict[str, pd.DataFrame],
    variant: StrategyVariant,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for component in variant.required_components:
        component_frame = signals_by_component[component].copy()
        _require_columns(component_frame, ["signal_id", "symbol", "known_at"], scope=component)
        component_frame["component"] = component
        component_frame["component_signal_id"] = component_frame["signal_id"].astype(str)
        component_frame["signal_id"] = (
            variant.name + ":" + component + ":" + component_frame["signal_id"].astype(str)
        )
        if "source" not in component_frame.columns:
            component_frame["source"] = component
        frames.append(component_frame)
    return pd.concat(frames, ignore_index=True)


def _summary_row_from_backtest(
    variant: StrategyVariant,
    result_summary: pd.DataFrame,
    data_start: str,
    data_end: str,
    trading_cost_bps: float,
    slippage_bps: float,
) -> dict[str, object]:
    base = _summary_base(
        variant=variant,
        status="ok" if not result_summary.empty else "no_trades",
        missing_components=(),
        data_start=data_start,
        data_end=data_end,
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
    )
    if result_summary.empty:
        return base
    for column in VARIANT_BACKTEST_SUMMARY_COLUMNS:
        base[column] = result_summary.iloc[0].get(column, pd.NA)
    return base


def _unavailable_summary_row(
    variant: StrategyVariant,
    missing_components: tuple[str, ...],
    data_start: str,
    data_end: str,
    trading_cost_bps: float,
    slippage_bps: float,
) -> dict[str, object]:
    return _summary_base(
        variant=variant,
        status="unavailable",
        missing_components=missing_components,
        data_start=data_start,
        data_end=data_end,
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
    )


def _error_summary_row(
    variant: StrategyVariant,
    message: str,
    data_start: str,
    data_end: str,
    trading_cost_bps: float,
    slippage_bps: float,
) -> dict[str, object]:
    row = _summary_base(
        variant=variant,
        status="error",
        missing_components=(),
        data_start=data_start,
        data_end=data_end,
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
    )
    row["missing_components"] = message
    return row


def _summary_base(
    variant: StrategyVariant,
    status: str,
    missing_components: tuple[str, ...],
    data_start: str,
    data_end: str,
    trading_cost_bps: float,
    slippage_bps: float,
) -> dict[str, object]:
    row = {
        "variant": variant.name,
        "description": variant.description,
        "status": status,
        "components": "+".join(variant.required_components),
        "missing_components": "+".join(missing_components),
        "data_start": data_start,
        "data_end": data_end,
        "trading_cost_bps": float(trading_cost_bps),
        "slippage_bps": float(slippage_bps),
    }
    for column in VARIANT_BACKTEST_SUMMARY_COLUMNS:
        row[column] = pd.NA
    return row


def _price_data_period(prices_by_symbol: dict[str, pd.DataFrame]) -> tuple[str, str]:
    dates = []
    for symbol, prices in prices_by_symbol.items():
        _require_columns(prices, ["date"], scope=symbol)
        parsed = pd.to_datetime(prices["date"], errors="raise")
        if not parsed.empty:
            dates.append(parsed)
    if not dates:
        raise StrategyVariantInputError("price data has no dates")
    combined = pd.concat(dates, ignore_index=True)
    return combined.min().date().isoformat(), combined.max().date().isoformat()


def _component_from_signal_id(signal_id: object) -> str | None:
    parts = str(signal_id).split(":", 2)
    if len(parts) < 3:
        return None
    return parts[1]


def _component_signal_id_from_signal_id(signal_id: object) -> str | None:
    parts = str(signal_id).split(":", 2)
    if len(parts) < 3:
        return None
    return parts[2]


def _require_columns(frame: pd.DataFrame, columns: list[str], scope: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise StrategyVariantInputError(f"{scope} missing required columns: {', '.join(missing)}")
