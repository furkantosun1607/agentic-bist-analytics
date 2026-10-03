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


@dataclass(frozen=True)
class RequirementCoverageEntry:
    requirement: str
    status: str
    evidence: str
    limitation: str


REQUIREMENT_COVERAGE: tuple[RequirementCoverageEntry, ...] = (
    RequirementCoverageEntry(
        requirement="Educational BIST 100 research system; no broker or investment advice",
        status="Met",
        evidence="README.md; reports/final_technical_report.md; reports/llm_agent_harness.md",
        limitation="System is research-only and does not execute market orders.",
    ),
    RequirementCoverageEntry(
        requirement="Fixed 30-stock BIST universe and sector map",
        status="Met",
        evidence="config/universe.csv; config/universe_dictionary.md",
        limitation="Historical BIST 100 membership over the full study period still requires external documentation.",
    ),
    RequirementCoverageEntry(
        requirement="Market data with XU100 benchmark and source metadata",
        status="Met",
        evidence="src/data.py; reports/market_cache_audit.md; reports/missing_symbols.csv",
        limitation="Raw local cache files under data/cache are ignored by git.",
    ),
    RequirementCoverageEntry(
        requirement="Technical indicator layer: SMA, EMA, KAMA, RSI, MACD, Bollinger, ATR, Supertrend, Ichimoku, support/resistance and volume",
        status="Met",
        evidence="src/indicators.py; src/events.py; reports/technical_reversals.md",
        limitation="Rules are intentionally simple and not optimized.",
    ),
    RequirementCoverageEntry(
        requirement="Mandatory scenario 1: sector laggard / catch-up",
        status="Met",
        evidence="src/research.py; reports/sector_catch_up.md",
        limitation="Several simplified sectors have limited peer coverage.",
    ),
    RequirementCoverageEntry(
        requirement="Mandatory scenario 2: weekday and multi-day patterns",
        status="Met",
        evidence="src/research.py; reports/weekday_patterns.md",
        limitation="Multiple-testing risk is documented; results remain historical observations.",
    ),
    RequirementCoverageEntry(
        requirement="Mandatory scenario 3: technical reversal events",
        status="Met",
        evidence="src/events.py; reports/technical_reversals.md",
        limitation="Optional divergence candidates are not treated as a separate optimized model.",
    ),
    RequirementCoverageEntry(
        requirement="Mandatory scenario 4: quarterly fundamentals and post-disclosure price reaction",
        status="Partial",
        evidence="src/fundamentals.py; src/yfinance_fundamentals.py; reports/quarterly_fundamentals.md",
        limitation="Fintables is not used; instructor-approved yfinance fallback and synthetic disclosure timestamps are used.",
    ),
    RequirementCoverageEntry(
        requirement="Point-in-time fundamentals, macro and news publication timestamp handling",
        status="Met",
        evidence="src/validation.py; src/context.py; reports/fundamentals_import_status.md; reports/macro_context_status.md",
        limitation="Synthetic financial disclosure timestamps are conservative assumptions, not exact KAP times.",
    ),
    RequirementCoverageEntry(
        requirement="Macro context: USD/TRY, EUR/TRY, TCMB policy, Fed policy and TUIK inflation",
        status="Partial",
        evidence="src/macro_context_fetch.py; reports/macro_context_fetch_status.md; reports/macro_context_status.md",
        limitation="FX is fetched with yfinance; TCMB/TUIK/FED records are curated static point-in-time records rather than live official API pulls.",
    ),
    RequirementCoverageEntry(
        requirement="Financial news and speech intelligence context",
        status="Partial",
        evidence="src/rss_news.py; src/news_context.py; reports/context_sources.md; reports/news_alias_matches.md",
        limitation="RSS news metadata is implemented; instructor-approved video/STT pipeline is not implemented.",
    ),
    RequirementCoverageEntry(
        requirement="Backtesting with signal timing, costs, slippage, benchmarks and risk metrics",
        status="Met",
        evidence="src/backtest.py; reports/backtest.md; reports/split_regime.md",
        limitation="Backtest is trade-level research output, not a capital-constrained portfolio simulation.",
    ),
    RequirementCoverageEntry(
        requirement="Out-of-sample / regime evaluation",
        status="Met",
        evidence="src/splits.py; reports/split_regime.md",
        limitation="Unseen start date is fixed in configuration and should be disclosed when rerun.",
    ),
    RequirementCoverageEntry(
        requirement="MCP-like deterministic tools and constrained tool permissions",
        status="Partial",
        evidence="src/mcp_server.py; reports/mcp_tools.md; src/harness.py; reports/harness_state_machine.md",
        limitation="Implements an MCP-like local registry, not a deployed external MCP transport server.",
    ),
    RequirementCoverageEntry(
        requirement="Stateful agent harness with evidence, quality gate, human review and replay",
        status="Met",
        evidence="src/harness.py; src/evidence.py; src/decision_log.py; reports/decision_log.md",
        limitation="Human review is represented as a reviewed educational project record.",
    ),
    RequirementCoverageEntry(
        requirement="Memory architecture: temporal, episodic and procedural memory",
        status="Partial",
        evidence="reports/decision_logs/decisions.jsonl; reports/decision_logs/llm_agent/decisions.jsonl; src/harness.py",
        limitation="Replayable episodic/procedural records exist; no separate database-backed memory service is implemented.",
    ),
    RequirementCoverageEntry(
        requirement="Strategy variants A-E",
        status="Partial",
        evidence="src/strategy_variants.py; reports/strategy_variants.md",
        limitation="Variants A-C are measured; D-E are unavailable because executable macro/news-video trade signals are not invented.",
    ),
    RequirementCoverageEntry(
        requirement="Agent harness experiments A-E",
        status="Partial",
        evidence="src/harness_variants.py; reports/harness_variants.md; reports/llm_agent_harness.md",
        limitation="A-E harness comparison is deterministic capability scoring; live Gemini explanation exists separately.",
    ),
    RequirementCoverageEntry(
        requirement="Python source code / notebooks and environment instructions",
        status="Met",
        evidence="src/; scripts/; notebooks/01_classroom_demo.ipynb; requirements.txt; README.md; .env.example",
        limitation="Notebook is a lightweight classroom walkthrough and does not embed raw cache artifacts or secrets.",
    ),
    RequirementCoverageEntry(
        requirement="Final technical report and classroom demonstration",
        status="Met",
        evidence="reports/final_technical_report.md; reports/demo_summary.md; ui/dashboard.html",
        limitation="Dashboard is static and informational; it does not run analyses itself.",
    ),
)


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
        status="measured_partial_local_cache",
        data_period="market cache 2021-01-04 to 2026-09-24",
        source="P35 executable technical, sector and fundamentals signals plus RSS context metadata",
        sample_size="5 variants; A-C measured, D-E unavailable; 42864 variant trade rows",
        assumptions="same data period, 10 bps cost and 5 bps slippage across A-E",
        limitations="macro and news/video executable signals are unavailable; RSS context is not a trade signal",
    ),
    ReportManifestEntry(
        report_name="Harness variants A-E",
        path="reports/harness_variants.md",
        status="measured_deterministic_no_live_llm",
        data_period="fixed question set in config/harness_questions.csv",
        source="deterministic harness capability fixture",
        sample_size="5 fixed questions across 5 harness variants",
        assumptions="compares harness controls, evidence gates, replay and human-review capability",
        limitations="does not call a live LLM and does not judge answer prose quality",
    ),
    ReportManifestEntry(
        report_name="LLM agent harness",
        path="reports/llm_agent_harness.md",
        status="optional_live_or_offline_llm_ready",
        data_period="committed local project evidence through current report artifacts",
        source="LLM explanation over deterministic evidence bundle and quality gate payload",
        sample_size="1 reviewed LLM harness decision record",
        assumptions="LLM returns constrained JSON and cannot calculate financial metrics",
        limitations="live prose quality depends on configured API key/model; offline fallback is deterministic",
    ),
    ReportManifestEntry(
        report_name="PDF requirement coverage",
        path="reports/pdf_requirement_coverage.md",
        status="pdf_alignment_matrix_ready",
        data_period="course PDF requirements reviewed against current local project artifacts",
        source="Engineering Economics Project 2026 PDF and local report inventory",
        sample_size=f"{len(REQUIREMENT_COVERAGE)} requirement coverage rows",
        assumptions="coverage statuses are explicit and do not convert limitations into completed work",
        limitations="coverage is a project-compliance map, not an empirical research result",
    ),
    ReportManifestEntry(
        report_name="Classroom demo notebook",
        path="notebooks/01_classroom_demo.ipynb",
        status="classroom_walkthrough_ready",
        data_period="current local report inventory and latest LLM harness artifact",
        source="notebook walkthrough over local reports, commands and dashboard",
        sample_size="one notebook with setup, workflow, report links, LLM output reader and limitations",
        assumptions="notebook is for classroom navigation and does not store secrets",
        limitations="notebook does not execute the full pipeline automatically",
    ),
    ReportManifestEntry(
        report_name="Decision log",
        path="reports/decision_log.md",
        status="reviewed_replay_ok",
        data_period="reviewed record created at 2026-09-25T12:00:00+00:00",
        source="harness snapshot, tool outputs and quality gate payloads",
        sample_size="1 reviewed educational decision record; replay status ok",
        assumptions="JSONL record requires output label, review, evidence hash and record hash",
        limitations="educational project evidence only; not an investment recommendation",
    ),
    ReportManifestEntry(
        report_name="Static dashboard",
        path="ui/dashboard.html",
        status="static_dashboard_ready",
        data_period="current local report inventory",
        source="local report manifest and LLM harness JSON output",
        sample_size="HTML dashboard with report cards and command checklist",
        assumptions="dashboard is regenerated after report or LLM harness updates",
        limitations="static UI only; it does not fetch live data or run server-side actions",
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


def write_requirement_coverage(
    output_path: str | Path = REPORTS_DIR / "pdf_requirement_coverage.md",
) -> Path:
    """Write a PDF-to-project requirement coverage matrix."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PDF Requirement Coverage Matrix",
        "",
        "This matrix maps the course PDF requirements to the current repository artifacts. It is a delivery-readiness aid, not a financial result.",
        "",
        "| PDF requirement | Status | Project evidence | Limitation / note |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(_coverage_table_rows())
    lines.extend(
        [
            "",
            "Status policy:",
            "- `Met`: implemented and documented with local artifacts.",
            "- `Partial`: materially supported, but one or more PDF details are not fully implemented.",
            "- `Unavailable/Documented Limitation`: intentionally not implemented or blocked by source access; no values are invented.",
            "",
            "Non-negotiable rule: missing Fintables, live official macro API, video/STT, and D-E executable trade signals remain explicit limitations.",
            "",
        ]
    )
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
        "Status: final PDF-alignment package is ready. Local market, fundamentals, macro and RSS artifacts are available; the four required research reports, backtest/risk report, unseen/regime report, partial A-E strategy comparison, deterministic harness comparison, optional LLM agent harness, PDF requirement coverage matrix, classroom demo notebook, static dashboard and reviewed decision replay have been generated.",
        "",
        "## Scope",
        "",
        "This project implements an educational BIST 100 research harness for a fixed 30-stock universe. Python modules perform deterministic calculations for data loading, validation, indicators, events, research scenarios, context records, backtesting, risk metrics, evidence bundles, stateful harness control, human-reviewed decision logs, strategy variants and harness variants.",
        "",
        "## Report Status",
        "",
        "The four scenario reports, backtest/risk report, unseen/regime report, A-C strategy variants, deterministic harness A-E comparison, optional LLM explanation run, PDF requirement coverage matrix, classroom demo notebook, static dashboard and reviewed decision replay have measured or generated outputs. RSS news context, local yfinance fundamentals and numeric macro context are ready as local artifacts, but D-E strategy variants remain unavailable until executable macro and news/video signals are defined.",
        "",
        "## Inconclusive Findings",
        "",
        "The four scenario reports, P35 backtest, P36 unseen/regime report and P37 A-C strategy variants contain local-cache measurements, but final strategy-level conclusions remain partial because macro and news/video executable signals are unavailable for D-E.",
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
        "- Evidence bundle, quality gate and replayable decision log with one reviewed record.",
        "- PDF requirement coverage matrix and classroom demo notebook for submission review.",
        "",
        "## PDF Requirement Coverage",
        "",
        "| PDF requirement | Status | Project evidence | Limitation / note |",
        "| --- | --- | --- | --- |",
        *_coverage_table_rows(),
        "",
        "## Limitations",
        "",
        "- Raw local macro, fundamentals, market and RSS cache files are not committed.",
        "- Instructor-approved video/STT context is not implemented in the current RSS-only flow.",
        "- Strategy variants D-E remain unavailable because executable macro/news-video trade signals are not invented.",
        "- Harness variants are measured with deterministic fixtures; the optional LLM harness can run live only when an API key is configured.",
        "- The static dashboard is informational and does not fetch live data.",
        "- The measured backtest is trade-level research output and not a portfolio allocation simulation.",
        "- No broker connection or investment advice is included.",
        "",
        "## Submission Status",
        "",
        "Final packaging artifacts have been refreshed. Before submission, rerun the documented commands if local cache artifacts are intentionally updated or if a fresh live Gemini explanation is required.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _coverage_table_rows() -> list[str]:
    rows: list[str] = []
    for entry in REQUIREMENT_COVERAGE:
        rows.append(
            f"| {_escape_table(entry.requirement)} | {_escape_table(entry.status)} | "
            f"{_escape_table(entry.evidence)} | {_escape_table(entry.limitation)} |"
        )
    return rows


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
