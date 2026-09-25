"""Report manifest and final technical narrative helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"


@dataclass(frozen=True)
class ReportManifestEntry:
    report_name: str
    path: str
    status: str
    data_period: str
    source: str
    sample_size: str
    assumptions: str
    limitations: str


REPORT_MANIFEST: tuple[ReportManifestEntry, ...] = (
    ReportManifestEntry(
        report_name="Market cache audit",
        path="reports/market_cache_audit.md",
        status="local_cache_audited",
        data_period="2021-01-04 to 2026-09-24 in current local cache",
        source="Yahoo Finance/yfinance local cache",
        sample_size="31 cached symbols audited; 30 universe symbols plus XU100 benchmark",
        assumptions="adjusted close available, local cache files are not committed",
        limitations="BIST 100 membership over the full period still requires external documentation",
    ),
    ReportManifestEntry(
        report_name="Sector catch-up",
        path="reports/sector_catch_up.md",
        status="measured_local_cache",
        data_period="2021-01-04 to 2026-09-24",
        source="Yahoo Finance/yfinance local market cache",
        sample_size="129192 observation rows",
        assumptions="20-day lookback, 5/10/20-day horizons, same-sector self-excluding peers",
        limitations="raw cache is ignored by git; many simplified sectors have limited peer coverage",
    ),
    ReportManifestEntry(
        report_name="Weekday and multi-day patterns",
        path="reports/weekday_patterns.md",
        status="measured_local_cache",
        data_period="2021-01-04 to 2026-09-24",
        source="Yahoo Finance/yfinance local market cache",
        sample_size="215320 observation rows; 50 summary rows",
        assumptions="1-5 trading-day holds, configured costs/slippage, optional regime split",
        limitations="multiple-testing risk; raw cache is ignored by git",
    ),
    ReportManifestEntry(
        report_name="Technical reversals",
        path="reports/technical_reversals.md",
        status="measured_local_cache",
        data_period="2021-01-04 to 2026-09-24",
        source="deterministic indicators/events from local OHLCV cache",
        sample_size="158444 observation rows; 30967 generated event rows; 1662 summary rows",
        assumptions="1/3/5/10-day post-event returns, combined same-day signals",
        limitations="event rules are simple and not optimized; raw cache is ignored by git",
    ),
    ReportManifestEntry(
        report_name="Quarterly fundamentals",
        path="reports/quarterly_fundamentals.md",
        status="measured_local_cache",
        data_period="disclosures 2025-02-09 to 2026-09-09; market cache through 2026-09-24",
        source="Yahoo Finance/yfinance quarterly statements with synthetic disclosure lag",
        sample_size="3057 observation rows; 160 fundamentals rows; 33 summary rows",
        assumptions="period_end plus configured disclosure lag, post-disclosure entry, bank/industrial metric separation",
        limitations="synthetic disclosure timestamps are conservative assumptions, not exact KAP times",
    ),
    ReportManifestEntry(
        report_name="Fundamentals fetch status",
        path="reports/fundamentals_fetch_status.md",
        status="local_yfinance_fetch_ready",
        data_period="local yfinance quarterly statements fetched on 2026-09-24",
        source="Yahoo Finance/yfinance",
        sample_size="160 rows across 30 fixed-universe tickers",
        assumptions="synthetic disclosure timestamp equals period_end plus 40 days at 18:30 Europe/Istanbul",
        limitations="raw local fundamentals CSV is ignored by git; timestamps are conservative assumptions",
    ),
    ReportManifestEntry(
        report_name="Fundamentals import status",
        path="reports/fundamentals_import_status.md",
        status="local_import_ready",
        data_period="2024-12-31 to 2026-07-31 local fundamentals periods",
        source="instructor-approved Yahoo Finance/yfinance fallback or manually prepared CSV",
        sample_size="160 valid rows; 30/30 universe ticker coverage",
        assumptions="synthetic disclosure timestamp equals period_end plus configured conservative lag",
        limitations="quarterly fundamentals report still needs measured run against market cache",
    ),
    ReportManifestEntry(
        report_name="Macro/news/video context",
        path="reports/context_sources.md",
        status="rss_and_macro_context_ready_no_video_required",
        data_period="RSS cache decision-time window; numeric macro context 2024-01-01 to 2026-09-24",
        source="Configured RSS feeds, yfinance FX and static curated TCMB/TUIK/Federal Reserve records",
        sample_size="RSS context rows generated from local cache; 1421 numeric macro rows generated locally",
        assumptions="published_timestamp <= decision_timestamp, 7-day default lookback, alias matches are context evidence",
        limitations="RSS source availability varies; alias matches are not sentiment or trade signals",
    ),
    ReportManifestEntry(
        report_name="Macro context fetch status",
        path="reports/macro_context_fetch_status.md",
        status="local_macro_fetch_ready",
        data_period="2024-01-01 to 2026-09-24 for yfinance FX plus 2026 static policy/inflation records",
        source="yfinance FX plus static curated TCMB/TUIK/Federal Reserve records",
        sample_size="1421 rows; 709 USD/TRY, 709 EUR/TRY and 3 static policy/inflation rows",
        assumptions="FX daily close is treated as knowable from the next local morning",
        limitations="TCMB/TUIK/FED static records are curated project inputs, not live API pulls",
    ),
    ReportManifestEntry(
        report_name="Macro context status",
        path="reports/macro_context_status.md",
        status="local_macro_context_ready",
        data_period="2024-01-01 to 2026-09-24 for yfinance FX plus 2026 static policy/inflation records",
        source="yfinance FX plus static curated TCMB/TUIK/Federal Reserve records",
        sample_size="1421 valid rows; 5/5 required indicators present",
        assumptions="requires observed period, publication timestamp, download timestamp and source URL per row",
        limitations="local macro CSV is generated artifact and is ignored by git; RSS macro aliases do not replace numeric macro records",
    ),
    ReportManifestEntry(
        report_name="Research run status",
        path="reports/research_run_status.md",
        status="four_reports_measured_local_cache",
        data_period="market cache 2021-01-04 to 2026-09-24; fundamentals disclosures 2025-02-09 to 2026-09-09",
        source="local market cache, yfinance fundamentals CSV, generated technical events",
        sample_size="4 reports generated; 506013 total observation rows",
        assumptions="same local cache and configured horizons/costs are reused across reports",
        limitations="raw input artifacts are ignored by git; measured reports are educational historical research",
    ),
    ReportManifestEntry(
        report_name="Backtest and risk",
        path="reports/backtest.md",
        status="measured_local_cache",
        data_period="market cache 2021-01-04 to 2026-09-24",
        source="fixed research signals from P34 observations and local OHLCV cache",
        sample_size="25819 signal rows; 25813 tradable rows; 30 symbols",
        assumptions="next-trading-day entry, horizon close exit, 10 bps cost, 5 bps slippage",
        limitations="trade-level risk only; overlapping trades are not capital-constrained portfolio simulation",
    ),
    ReportManifestEntry(
        report_name="Unseen period and regime split",
        path="reports/split_regime.md",
        status="measured_local_cache",
        data_period="signal dates 2021-01-29 to 2026-09-16; unseen starts 2025-10-01",
        source="P35 backtest trades and XU100 local benchmark cache",
        sample_size="25813 tradable rows; 20909 selection rows; 4904 unseen rows",
        assumptions="known_at-based split, 20-day XU100 rising/falling regime labels",
        limitations="trade-level stability only; strategy variant selection remains later phase",
    ),
    ReportManifestEntry(
        report_name="Strategy variants A-E",
        path="reports/strategy_variants.md",
        status="engine_ready_no_measured_result",
        data_period="not available until verified strategy signals are generated",
        source="technical, sector, fundamentals, macro and verified context signals planned",
        sample_size="not measured",
        assumptions="same data period and costs across A-E",
        limitations="missing-source variants are unavailable, not inferred",
    ),
    ReportManifestEntry(
        report_name="Harness variants A-E",
        path="reports/harness_variants.md",
        status="engine_ready_no_live_llm_run",
        data_period="fixed question set not finalized",
        source="deterministic capability comparison",
        sample_size="synthetic unit-test questions only",
        assumptions="compares harness capabilities, not financial returns",
        limitations="no live LLM run is reported",
    ),
    ReportManifestEntry(
        report_name="Decision log",
        path="reports/decision_log.md",
        status="schema_ready_no_live_decision",
        data_period="not applicable",
        source="harness snapshot, tool outputs and quality gate payloads",
        sample_size="0 live reviewed decisions committed",
        assumptions="JSONL records require output label, review and evidence hash",
        limitations="unit tests use synthetic records only",
    ),
)


def validate_report_manifest(
    manifest: tuple[ReportManifestEntry, ...] = REPORT_MANIFEST,
    project_root: Path = PROJECT_ROOT,
) -> list[str]:
    """Validate report inventory completeness without inventing measured results."""

    errors: list[str] = []
    for entry in manifest:
        report_path = project_root / entry.path
        if not report_path.exists():
            errors.append(f"missing report: {entry.path}")
        for field_name in (
            "status",
            "data_period",
            "source",
            "sample_size",
            "assumptions",
            "limitations",
        ):
            if not getattr(entry, field_name).strip():
                errors.append(f"{entry.report_name} missing {field_name}")
    return errors


def write_report_index(output_path: str | Path = REPORTS_DIR / "report_index.md") -> Path:
    """Write a report inventory with required metadata."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Report Index",
        "",
        "This index tracks report readiness and prevents unverified data from being presented as measured output.",
        "",
        "| Report | Status | Data period | Source | Sample size | Assumptions | Limitations |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in REPORT_MANIFEST:
        lines.append(
            f"| {entry.report_name} | {entry.status} | {entry.data_period} | "
            f"{entry.source} | {entry.sample_size} | {entry.assumptions} | {entry.limitations} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_final_technical_report(
    output_path: str | Path = REPORTS_DIR / "final_technical_report.md",
) -> Path:
    """Write the final technical narrative for the current implementation state."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Final Technical Report",
        "",
        "Status: implementation infrastructure is complete through measured report orchestration. Local market, fundamentals, macro and RSS artifacts are available; the four required research reports, backtest/risk report and unseen/regime report have been generated from local cache.",
        "",
        "## Scope",
        "",
        "This project implements an educational BIST 100 research harness for a fixed 30-stock universe. Python modules perform deterministic calculations for data loading, validation, indicators, events, research scenarios, context records, backtesting, risk metrics, evidence bundles, stateful harness control, human-reviewed decision logs, strategy variants and harness variants.",
        "",
        "## Report Status",
        "",
        "The four scenario reports, backtest/risk report and unseen/regime report have measured local-cache outputs. RSS news context, local yfinance fundamentals and numeric macro context are ready as local artifacts, but strategy variants and final measured strategy outputs are still missing.",
        "",
        "## Inconclusive Findings",
        "",
        "The four scenario reports, P35 backtest and P36 unseen/regime report contain local-cache measurements, but strategy-level conclusions remain inconclusive until P37 runs strategy variants on verified signals.",
        "",
        "## Key Controls",
        "",
        "- Fixed 30-stock universe and data dictionary.",
        "- Point-in-time validation and future leakage blocking.",
        "- Disclosure timestamp handling for fundamentals.",
        "- Source metadata requirements for macro, news and video context.",
        "- Nonzero cost and slippage assumptions.",
        "- Unseen-period and regime split helpers.",
        "- Deterministic MCP-like tool surface.",
        "- Stateful harness with permitted tool rules.",
        "- Evidence bundle, quality gate and replayable decision log.",
        "",
        "## Limitations",
        "",
        "- Raw local macro, fundamentals, market and RSS cache files are not committed.",
        "- Approved video context and final measured strategy outputs are not committed.",
        "- Strategy and harness variant reports are engines, not live experiment results.",
        "- The measured backtest is trade-level research output and not a portfolio allocation simulation.",
        "- No broker connection or investment advice is included.",
        "",
        "## Next Step",
        "",
        "P37 should run measured strategy variant comparisons, then later phases should refresh harness experiments, decision review and final packaging.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
