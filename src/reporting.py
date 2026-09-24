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
        status="infrastructure_ready_no_measured_result",
        data_period="not available until market cache is generated",
        source="Yahoo Finance/yfinance cache planned",
        sample_size="not measured",
        assumptions="20-day lookback, 5/10/20-day horizons, same-sector self-excluding peers",
        limitations="live/cache market data is not committed",
    ),
    ReportManifestEntry(
        report_name="Weekday and multi-day patterns",
        path="reports/weekday_patterns.md",
        status="infrastructure_ready_no_measured_result",
        data_period="not available until market cache is generated",
        source="Yahoo Finance/yfinance cache planned",
        sample_size="not measured",
        assumptions="1-5 trading-day holds, configured costs/slippage, optional regime split",
        limitations="multiple-testing risk and no live/cache market data yet",
    ),
    ReportManifestEntry(
        report_name="Technical reversals",
        path="reports/technical_reversals.md",
        status="infrastructure_ready_no_measured_result",
        data_period="not available until market cache is generated",
        source="deterministic indicators/events from cached OHLCV planned",
        sample_size="not measured",
        assumptions="1/3/5/10-day post-event returns, combined same-day signals",
        limitations="event rules are simple and no live/cache market data yet",
    ),
    ReportManifestEntry(
        report_name="Quarterly fundamentals",
        path="reports/quarterly_fundamentals.md",
        status="infrastructure_ready_no_measured_result",
        data_period="not available until verified disclosures and market cache are generated",
        source="Fintables source planned, access/licensing pending verification",
        sample_size="not measured",
        assumptions="post-disclosure entry, bank/industrial metric separation",
        limitations="verified fundamentals data is not committed",
    ),
    ReportManifestEntry(
        report_name="Macro/news/video context",
        path="reports/context_sources.md",
        status="rss_context_ready_no_video_required",
        data_period="RSS cache decision-time window; macro/manual context not populated",
        source="Configured RSS feeds plus planned TCMB/EVDS, TUIK, Federal Reserve and optional video context",
        sample_size="RSS context rows generated from local cache; live cache files are not committed",
        assumptions="published_timestamp <= decision_timestamp, 7-day default lookback, alias matches are context evidence",
        limitations="RSS source availability varies; alias matches are not sentiment or trade signals",
    ),
    ReportManifestEntry(
        report_name="Backtest and risk",
        path="reports/backtest.md",
        status="engine_ready_no_measured_result",
        data_period="not available until verified signals and market cache are generated",
        source="verified signal records and cached OHLCV planned",
        sample_size="not measured",
        assumptions="next-trading-day entry, horizon close exit, 10 bps cost, 5 bps slippage",
        limitations="trade-level Sharpe only; no live strategy outputs yet",
    ),
    ReportManifestEntry(
        report_name="Unseen period and regime split",
        path="reports/split_regime.md",
        status="helpers_ready_no_measured_result",
        data_period="unseen_start_date not fixed",
        source="benchmark price history planned",
        sample_size="not measured",
        assumptions="benchmark-based rising/falling regime labels",
        limitations="unseen date waits for verified data coverage",
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
        "Status: implementation infrastructure is complete through report orchestration; live/cache datasets and verified source records are still required before measured financial conclusions can be reported.",
        "",
        "## Scope",
        "",
        "This project implements an educational BIST 100 research harness for a fixed 30-stock universe. Python modules perform deterministic calculations for data loading, validation, indicators, events, research scenarios, context records, backtesting, risk metrics, evidence bundles, stateful harness control, human-reviewed decision logs, strategy variants and harness variants.",
        "",
        "## Report Status",
        "",
        "The scenario reports, context report, backtest/risk report and variant reports are present as reproducible infrastructure reports. RSS news context can be generated from local cache, but the repository still does not contain verified fundamentals, macro records, approved video context or final measured strategy outputs.",
        "",
        "## Inconclusive Findings",
        "",
        "All empirical findings are currently inconclusive. The repository contains calculation engines and test coverage, not committed live/cache data outputs. Any final claim about returns, alpha, risk or strategy superiority must wait until verified datasets are loaded and the report writers are rerun.",
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
        "- Market price, XU100 and RSS cache files are not committed.",
        "- Verified fundamentals, macro, news and video records are not committed.",
        "- Strategy and harness variant reports are engines, not live experiment results.",
        "- No broker connection or investment advice is included.",
        "",
        "## Next Step",
        "",
        "P23 should add install/run documentation and one demo command. A measured classroom demo should first generate or load verified cache data, then rerun the relevant report writers.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
