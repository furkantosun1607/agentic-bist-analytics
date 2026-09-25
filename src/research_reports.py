"""Run the four required research reports from local cached artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data import UniverseMember, read_price_cache
from src.events import detect_all_events
from src.fundamentals import load_fundamentals_csv
from src.fundamentals_status import DEFAULT_FUNDAMENTALS_INPUT_PATH
from src.indicators import add_all_indicators
from src.research import (
    QuarterlyFundamentalsResult,
    ResearchError,
    SectorCatchUpResult,
    TechnicalReversalResult,
    WeekdayPatternResult,
    empty_quarterly_fundamentals_frame,
    empty_quarterly_fundamentals_summary_frame,
    run_quarterly_fundamentals,
    run_sector_catch_up,
    run_technical_reversals,
    run_weekday_patterns,
    write_quarterly_fundamentals_report,
    write_sector_catch_up_report,
    write_technical_reversals_report,
    write_weekday_patterns_report,
)
from src.settings import Settings, load_settings


@dataclass(frozen=True)
class ResearchReportRunSummary:
    report_name: str
    path: Path
    status: str
    observation_rows: int
    summary_rows: int | None = None
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchReportRunResult:
    reports: tuple[ResearchReportRunSummary, ...]
    missing_price_symbols: tuple[str, ...]
    generated_event_rows: int
    fundamentals_rows: int


def run_research_reports_from_settings(
    settings: Settings | None = None,
    fundamentals_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
) -> ResearchReportRunResult:
    """Run all four scenario reports from configured local cache paths."""

    active_settings = settings or load_settings()
    from src.data import load_universe

    universe = load_universe(active_settings.paths.universe)
    return run_research_reports(
        universe=universe,
        cache_dir=active_settings.paths.cache_dir,
        reports_dir=active_settings.paths.reports_dir,
        benchmark_symbol=active_settings.market_data.benchmark_symbol,
        fundamentals_path=fundamentals_path,
        horizons=tuple(active_settings.backtest.horizons),
        trading_cost_bps=active_settings.backtest.trading_cost_bps,
        slippage_bps=active_settings.backtest.slippage_bps,
        regime_lookback_days=active_settings.experiment.regime_lookback_days,
        unseen_start_date=active_settings.experiment.unseen_start_date,
    )


def run_research_reports(
    universe: list[UniverseMember],
    cache_dir: str | Path,
    reports_dir: str | Path,
    benchmark_symbol: str,
    fundamentals_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
    horizons: tuple[int, ...] = (1, 3, 5, 10, 20),
    trading_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
    regime_lookback_days: int = 20,
    unseen_start_date: str | None = None,
) -> ResearchReportRunResult:
    """Run sector, calendar, technical and fundamentals reports."""

    report_path = Path(reports_dir)
    prices_by_symbol, missing_symbols = load_cached_universe_prices(universe, cache_dir)
    benchmark_prices = _read_optional_price_cache(cache_dir, benchmark_symbol)
    scenario_horizons = tuple(horizon for horizon in (5, 10, 20) if horizon in horizons) or (5, 10, 20)
    reversal_horizons = tuple(horizon for horizon in (1, 3, 5, 10) if horizon in horizons) or (1, 3, 5, 10)
    fundamentals_horizons = tuple(horizon for horizon in (1, 5, 20) if horizon in horizons) or (1, 5, 20)

    summaries: list[ResearchReportRunSummary] = []

    sector_result = run_sector_catch_up(
        prices_by_symbol=prices_by_symbol,
        universe=universe,
        lookback_days=20,
        horizons=scenario_horizons,
    )
    sector_output = write_sector_catch_up_report(
        sector_result,
        report_path / "sector_catch_up.md",
        lookback_days=20,
    )
    _append_run_metadata(
        sector_output,
        data_source="local Yahoo Finance/yfinance market cache",
        assumptions="20-day lookback; 5/10/20-day horizons; same-sector self-excluding peers",
        context_note="Fundamentals, macro and RSS context are available as separate evidence metadata and are not used to compute this signal.",
    )
    summaries.append(_summary_from_sector("sector_catch_up", sector_output, sector_result))

    weekday_result = run_weekday_patterns(
        prices_by_symbol=prices_by_symbol,
        benchmark_prices=benchmark_prices,
        holding_days=(1, 2, 3, 4, 5),
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
        regime_lookback_days=regime_lookback_days,
        unseen_start_date=unseen_start_date,
    )
    weekday_output = write_weekday_patterns_report(
        weekday_result,
        report_path / "weekday_patterns.md",
    )
    _append_run_metadata(
        weekday_output,
        data_source="local Yahoo Finance/yfinance market cache",
        assumptions=f"1-5 day holds; cost {trading_cost_bps} bps; slippage {slippage_bps} bps; benchmark regime from {benchmark_symbol if benchmark_prices is not None else 'symbol history'}",
        context_note="Multiple-testing risk remains; unseen period is only reported when configured.",
    )
    summaries.append(_summary_from_weekday("weekday_patterns", weekday_output, weekday_result))

    events_by_symbol, event_errors = build_events_from_prices(prices_by_symbol)
    technical_result = run_technical_reversals(
        prices_by_symbol=prices_by_symbol,
        events_by_symbol=events_by_symbol,
        benchmark_prices=benchmark_prices,
        horizons=reversal_horizons,
        regime_lookback_days=regime_lookback_days,
    )
    if event_errors:
        technical_result = TechnicalReversalResult(
            observations=technical_result.observations,
            summary=technical_result.summary,
            errors=(
                *technical_result.errors,
                *(ResearchError(scope=symbol, message=message) for symbol, message in event_errors),
            ),
        )
    technical_output = write_technical_reversals_report(
        technical_result,
        report_path / "technical_reversals.md",
    )
    _append_run_metadata(
        technical_output,
        data_source="local market cache with deterministic technical indicators/events",
        assumptions="events become tradable after daily close; entry is next available trading day",
        context_note="Macro/RSS/fundamentals are not used as event triggers in this report.",
    )
    summaries.append(
        _summary_from_technical("technical_reversals", technical_output, technical_result)
    )

    fundamentals_result, fundamentals_rows = _run_quarterly_fundamentals_or_inconclusive(
        fundamentals_path=fundamentals_path,
        universe=universe,
        prices_by_symbol=prices_by_symbol,
        benchmark_prices=benchmark_prices,
        horizons=fundamentals_horizons,
    )
    fundamentals_output = write_quarterly_fundamentals_report(
        fundamentals_result,
        report_path / "quarterly_fundamentals.md",
    )
    _append_run_metadata(
        fundamentals_output,
        data_source="local yfinance fundamentals CSV with synthetic disclosure lag and local market cache",
        assumptions="disclosure timestamp is period_end plus configured conservative lag; entry is first trading day after disclosure",
        context_note="Macro and RSS context are available as evidence metadata but are not used to calculate returns.",
    )
    summaries.append(
        _summary_from_fundamentals(
            "quarterly_fundamentals",
            fundamentals_output,
            fundamentals_result,
        )
    )

    status_output = write_research_run_status(
        ResearchReportRunResult(
            reports=tuple(summaries),
            missing_price_symbols=tuple(missing_symbols),
            generated_event_rows=sum(len(events) for events in events_by_symbol.values()),
            fundamentals_rows=fundamentals_rows,
        ),
        report_path / "research_run_status.md",
    )
    _ = status_output
    return ResearchReportRunResult(
        reports=tuple(summaries),
        missing_price_symbols=tuple(missing_symbols),
        generated_event_rows=sum(len(events) for events in events_by_symbol.values()),
        fundamentals_rows=fundamentals_rows,
    )


def load_cached_universe_prices(
    universe: list[UniverseMember],
    cache_dir: str | Path,
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Load local cached price histories for the fixed universe."""

    prices: dict[str, pd.DataFrame] = {}
    missing: list[str] = []
    for member in universe:
        try:
            prices[member.yahoo_symbol] = read_price_cache(cache_dir, member.yahoo_symbol)
        except Exception:
            missing.append(member.yahoo_symbol)
    return prices, missing


def build_events_from_prices(
    prices_by_symbol: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], list[tuple[str, str]]]:
    """Compute indicators and technical events for every loaded symbol."""

    events_by_symbol: dict[str, pd.DataFrame] = {}
    errors: list[tuple[str, str]] = []
    for symbol, prices in prices_by_symbol.items():
        try:
            enriched = add_all_indicators(prices)
            detected = detect_all_events(enriched, symbol=symbol)
        except Exception as exc:
            errors.append((symbol, str(exc)))
            continue

        if detected.errors:
            errors.extend((symbol, f"{error.detector}: {error.message}") for error in detected.errors)
        events_by_symbol[symbol] = detected.events
    return events_by_symbol, errors


def write_research_run_status(
    result: ResearchReportRunResult,
    output_path: str | Path,
) -> Path:
    """Write a compact status page for the P34 research report run."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Research Run Status",
        "",
        "Status: generated from local cached artifacts.",
        "",
        f"Generated technical event rows: {result.generated_event_rows}",
        f"Fundamentals rows loaded: {result.fundamentals_rows}",
        f"Missing price symbols: {', '.join(result.missing_price_symbols) or 'none'}",
        "",
        "## Reports",
        "",
        "| Report | Status | Observation rows | Summary rows | Errors |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for report in result.reports:
        errors = "; ".join(report.errors) if report.errors else "none"
        summary_rows = report.summary_rows if report.summary_rows is not None else "n/a"
        lines.append(
            f"| {report.report_name} | {report.status} | {report.observation_rows} | "
            f"{summary_rows} | {errors} |"
        )
    lines.extend(
        [
            "",
            "Limitations:",
            "- Raw market, fundamentals, macro and RSS cache artifacts are local and ignored by git.",
            "- These reports are historical educational research outputs, not investment advice.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _run_quarterly_fundamentals_or_inconclusive(
    fundamentals_path: str | Path,
    universe: list[UniverseMember],
    prices_by_symbol: dict[str, pd.DataFrame],
    benchmark_prices: pd.DataFrame | None,
    horizons: tuple[int, ...],
) -> tuple[QuarterlyFundamentalsResult, int]:
    path = Path(fundamentals_path)
    if not path.exists():
        return (
            QuarterlyFundamentalsResult(
                observations=empty_quarterly_fundamentals_frame(),
                summary=empty_quarterly_fundamentals_summary_frame(),
                errors=(
                    ResearchError(
                        scope="quarterly_fundamentals",
                        message=f"missing fundamentals CSV: {path}",
                    ),
                ),
            ),
            0,
        )

    imported = load_fundamentals_csv(path, universe)
    if imported.records.empty:
        return (
            QuarterlyFundamentalsResult(
                observations=empty_quarterly_fundamentals_frame(),
                summary=empty_quarterly_fundamentals_summary_frame(),
                errors=(
                    *(
                        ResearchError(scope="fundamentals_import", message=error.message)
                        for error in imported.errors
                    ),
                    ResearchError(scope="quarterly_fundamentals", message="no valid fundamentals rows"),
                ),
            ),
            0,
        )

    result = run_quarterly_fundamentals(
        fundamentals=imported.records,
        prices_by_symbol=prices_by_symbol,
        benchmark_prices=benchmark_prices,
        horizons=horizons,
    )
    if imported.errors:
        result = QuarterlyFundamentalsResult(
            observations=result.observations,
            summary=result.summary,
            errors=(
                *result.errors,
                *(
                    ResearchError(scope="fundamentals_import", message=error.message)
                    for error in imported.errors
                ),
            ),
        )
    return result, len(imported.records)


def _read_optional_price_cache(cache_dir: str | Path, symbol: str) -> pd.DataFrame | None:
    try:
        return read_price_cache(cache_dir, symbol)
    except Exception:
        return None


def _append_run_metadata(
    path: Path,
    data_source: str,
    assumptions: str,
    context_note: str,
) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n## Run Metadata\n\n")
        handle.write(f"- Data source: {data_source}.\n")
        handle.write(f"- Assumptions: {assumptions}.\n")
        handle.write(f"- Context note: {context_note}\n")


def _summary_from_sector(
    name: str,
    path: Path,
    result: SectorCatchUpResult,
) -> ResearchReportRunSummary:
    return ResearchReportRunSummary(
        report_name=name,
        path=path,
        status="measured" if not result.observations.empty else "inconclusive",
        observation_rows=len(result.observations),
        errors=tuple(f"{error.scope}: {error.message}" for error in result.errors),
    )


def _summary_from_weekday(
    name: str,
    path: Path,
    result: WeekdayPatternResult,
) -> ResearchReportRunSummary:
    return ResearchReportRunSummary(
        report_name=name,
        path=path,
        status="measured" if not result.observations.empty else "inconclusive",
        observation_rows=len(result.observations),
        summary_rows=len(result.summary),
        errors=tuple(f"{error.scope}: {error.message}" for error in result.errors),
    )


def _summary_from_technical(
    name: str,
    path: Path,
    result: TechnicalReversalResult,
) -> ResearchReportRunSummary:
    return ResearchReportRunSummary(
        report_name=name,
        path=path,
        status="measured" if not result.observations.empty else "inconclusive",
        observation_rows=len(result.observations),
        summary_rows=len(result.summary),
        errors=tuple(f"{error.scope}: {error.message}" for error in result.errors),
    )


def _summary_from_fundamentals(
    name: str,
    path: Path,
    result: QuarterlyFundamentalsResult,
) -> ResearchReportRunSummary:
    return ResearchReportRunSummary(
        report_name=name,
        path=path,
        status="measured" if not result.observations.empty else "inconclusive",
        observation_rows=len(result.observations),
        summary_rows=len(result.summary),
        errors=tuple(f"{error.scope}: {error.message}" for error in result.errors),
    )
