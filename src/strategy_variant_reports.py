"""Measured strategy variant orchestration from local fixed research signals."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest_reports import run_backtests
from src.data import UniverseMember, load_universe, read_price_cache
from src.fundamentals_status import DEFAULT_FUNDAMENTALS_INPUT_PATH
from src.news_context import DEFAULT_NEWS_CONTEXT_OUTPUT_PATH
from src.research_reports import load_cached_universe_prices
from src.settings import Settings, load_settings
from src.strategy_variants import (
    StrategyVariantComparisonResult,
    compare_strategy_variants,
    write_strategy_variants_report,
)


EXECUTABLE_SOURCE_TO_COMPONENT = {
    "technical_reversal_fixed": "technical",
    "sector_catch_up_laggard": "sector",
    "fundamentals_positive_change": "fundamentals",
}
PLANNED_NON_EXECUTABLE_COMPONENTS = ("macro", "news_video")


@dataclass(frozen=True)
class StrategyVariantRunResult:
    status: str
    comparison: StrategyVariantComparisonResult
    component_signal_counts: dict[str, int]
    unavailable_components: tuple[str, ...]
    rss_context_path: Path | None
    output_path: Path


def run_strategy_variants_from_settings(
    settings: Settings | None = None,
    fundamentals_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
    rss_context_path: str | Path = DEFAULT_NEWS_CONTEXT_OUTPUT_PATH,
) -> StrategyVariantRunResult:
    """Run P37 strategy variant comparison from configured local artifacts."""

    active_settings = settings or load_settings()
    universe = load_universe(active_settings.paths.universe)
    return run_strategy_variants(
        universe=universe,
        cache_dir=active_settings.paths.cache_dir,
        reports_dir=active_settings.paths.reports_dir,
        benchmark_symbol=active_settings.market_data.benchmark_symbol,
        fundamentals_path=fundamentals_path,
        rss_context_path=rss_context_path,
        horizons=tuple(active_settings.backtest.horizons),
        trading_cost_bps=float(active_settings.backtest.trading_cost_bps),
        slippage_bps=float(active_settings.backtest.slippage_bps),
        regime_lookback_days=int(active_settings.experiment.regime_lookback_days),
    )


def run_strategy_variants(
    universe: list[UniverseMember],
    cache_dir: str | Path,
    reports_dir: str | Path,
    benchmark_symbol: str,
    fundamentals_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
    rss_context_path: str | Path | None = DEFAULT_NEWS_CONTEXT_OUTPUT_PATH,
    horizons: tuple[int, ...] = (1, 3, 5, 10, 20),
    trading_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
    regime_lookback_days: int = 20,
) -> StrategyVariantRunResult:
    """Assemble executable components, compare A-E variants and write the report."""

    report_path = Path(reports_dir)
    prices_by_symbol, _ = load_cached_universe_prices(universe, cache_dir)
    benchmark_prices = _read_optional_price_cache(cache_dir, benchmark_symbol)
    symbol_to_sector = {member.yahoo_symbol: member.sector for member in universe}
    backtest_run = run_backtests(
        universe=universe,
        cache_dir=cache_dir,
        reports_dir=reports_dir,
        benchmark_symbol=benchmark_symbol,
        fundamentals_path=fundamentals_path,
        horizons=horizons,
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
        regime_lookback_days=regime_lookback_days,
    )
    signals_by_component = assemble_strategy_component_signals(backtest_run.signals)
    rss_context = _existing_rss_context_path(rss_context_path)
    comparison = compare_strategy_variants(
        signals_by_component=signals_by_component,
        prices_by_symbol=prices_by_symbol,
        benchmark_prices=benchmark_prices,
        symbol_to_sector=symbol_to_sector,
        rss_context=rss_context,
        default_horizon=_preferred_horizon(horizons, preferred=5),
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
    )
    output_path = write_strategy_variants_report(comparison, report_path / "strategy_variants.md")
    result = StrategyVariantRunResult(
        status=_run_status(comparison),
        comparison=comparison,
        component_signal_counts={
            component: len(signals) for component, signals in sorted(signals_by_component.items())
        },
        unavailable_components=_unavailable_executable_components(signals_by_component),
        rss_context_path=rss_context,
        output_path=output_path,
    )
    _append_strategy_variant_metadata(result)
    return result


def assemble_strategy_component_signals(signals: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Map fixed P35 signal sources to executable strategy components."""

    if signals is None or signals.empty:
        return {}

    signals_by_component: dict[str, pd.DataFrame] = {}
    for source, component in EXECUTABLE_SOURCE_TO_COMPONENT.items():
        selected = signals[signals["source"] == source].copy()
        if selected.empty:
            continue
        selected["source"] = component
        signals_by_component[component] = selected.reset_index(drop=True)
    return signals_by_component


def _append_strategy_variant_metadata(result: StrategyVariantRunResult) -> None:
    lines = [
        "",
        "## Measured Variant Run",
        "",
        f"Status: {result.status}.",
        "Signal policy: executable components are mapped from fixed P35 signals without selecting on future returns.",
        "Component policy: weekday research signals are not counted as A-E strategy components; RSS context metadata is not a trade signal.",
        "",
        "## Component Signal Counts",
        "",
    ]
    if result.component_signal_counts:
        rows = pd.DataFrame(
            [
                {"component": component, "signal_count": count}
                for component, count in result.component_signal_counts.items()
            ]
        )
        lines.extend([rows.to_markdown(index=False), ""])
    else:
        lines.extend(["No executable component signals were assembled.", ""])

    if result.unavailable_components:
        lines.extend(["## Unavailable Executable Components", ""])
        lines.extend(f"- `{component}`" for component in result.unavailable_components)
        lines.append("")

    if result.rss_context_path is not None:
        lines.extend(
            [
                "## RSS Context Metadata",
                "",
                f"RSS context path: `{_display_path(result.rss_context_path)}`.",
                "RSS context is included only as Variant E evidence metadata and does not create `news_video` trade signals.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## RSS Context Metadata",
                "",
                "RSS context file is missing; Variant E records RSS context as unavailable.",
                "",
            ]
        )

    lines.extend(
        [
            "Measured-run limitations:",
            "- Variants D and E remain unavailable until executable macro and news/video signals are defined.",
            "- Available variants are trade-level historical research outputs, not investment recommendations.",
            "",
        ]
    )
    with result.output_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def _run_status(comparison: StrategyVariantComparisonResult) -> str:
    if comparison.summary.empty:
        return "inconclusive"
    statuses = set(comparison.summary["status"].astype(str))
    if "ok" in statuses and "unavailable" in statuses:
        return "measured_partial"
    if "ok" in statuses:
        return "measured"
    return "inconclusive"


def _unavailable_executable_components(
    signals_by_component: dict[str, pd.DataFrame],
) -> tuple[str, ...]:
    unavailable = [
        component
        for component in PLANNED_NON_EXECUTABLE_COMPONENTS
        if component not in signals_by_component or signals_by_component[component].empty
    ]
    return tuple(unavailable)


def _existing_rss_context_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    return candidate if candidate.exists() else None


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


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
