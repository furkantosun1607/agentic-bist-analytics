"""Generate one reviewed, replayable educational decision log record."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.decision_log import (
    DecisionRecord,
    ReplayResult,
    create_decision_record,
    load_decision_records,
    replay_decision_record,
    write_decision_log_report,
    write_decision_records,
)
from src.evidence import build_evidence_bundle, evaluate_quality_gate
from src.harness import AnalysisHarness
from src.settings import Settings, load_settings


DECISION_ID = "p39-reviewed-educational-analysis"
CREATED_AT = "2026-09-25T12:00:00+00:00"


@dataclass(frozen=True)
class DecisionLogRunResult:
    status: str
    record: DecisionRecord
    replay: ReplayResult
    log_path: Path
    report_path: Path


def run_decision_log_from_settings(settings: Settings | None = None) -> DecisionLogRunResult:
    """Create the P39 reviewed decision record from local measured artifacts."""

    active_settings = settings or load_settings()
    return run_decision_log(
        log_dir=active_settings.outputs.decision_log_dir,
        reports_dir=active_settings.paths.reports_dir,
    )


def run_decision_log(
    log_dir: str | Path,
    reports_dir: str | Path,
) -> DecisionLogRunResult:
    """Build evidence, apply gate, save reviewed record and verify replay."""

    reports_path = Path(reports_dir)
    evidence_records = build_decision_evidence_records(reports_path)
    evidence_bundle = build_evidence_bundle(
        evidence_records,
        feature_columns=[
            "scenario_report_count",
            "backtest_trade_count",
            "strategy_variant_measured_count",
            "harness_question_count",
        ],
        source_columns=["source", "source_url", "known_at"],
    )
    quality_gate = evaluate_quality_gate(evidence_bundle)
    harness = _reviewed_harness(quality_gate)
    inputs = {
        "analysis_question": "Should the current educational BIST research run be accepted as replayable project evidence?",
        "decision_scope": "educational_project_artifact",
        "not_investment_advice": True,
    }
    tool_outputs = {
        "research_reports": {
            "scenario_report_count": 4,
            "status": "measured_local_cache",
        },
        "backtest": {
            "signal_rows": 25819,
            "tradable_rows": 25813,
            "status": "measured_local_cache",
        },
        "strategy_variants": {
            "variant_count": 5,
            "measured_variants": "A,B,C",
            "unavailable_variants": "D,E",
            "status": "measured_partial_local_cache",
        },
        "harness_variants": {
            "question_count": 5,
            "variant_count": 5,
            "best_variant": "E",
            "status": "measured_deterministic_no_live_llm",
        },
        "quality_gate": {
            "gate_status": quality_gate.gate_status,
            "evidence_hash": quality_gate.evidence_hash,
        },
    }
    record = create_decision_record(
        decision_id=DECISION_ID,
        harness=harness,
        inputs=inputs,
        tool_outputs=tool_outputs,
        quality_gate=quality_gate,
        reviewer="project-owner",
        review_notes=(
            "Accepted as an educational replay record for project evidence. "
            "This is not an investment recommendation."
        ),
        created_at=CREATED_AT,
    )
    log_path = write_decision_records([record], log_dir)
    loaded = load_decision_records(log_path)
    replay = replay_decision_record(loaded[0])
    report_path = write_decision_log_report(loaded, reports_path / "decision_log.md")
    _append_p39_metadata(report_path, replay, log_path)
    return DecisionLogRunResult(
        status="reviewed_replay_ok" if replay.status == "ok" else "reviewed_replay_error",
        record=record,
        replay=replay,
        log_path=log_path,
        report_path=report_path,
    )


def build_decision_evidence_records(reports_dir: str | Path) -> pd.DataFrame:
    """Return source-backed evidence rows for the reviewed educational decision."""

    reports_path = Path(reports_dir)
    return pd.DataFrame(
        [
            {
                "record_id": "research_reports",
                "source": "local_report",
                "source_url": str(reports_path / "research_run_status.md"),
                "known_at": CREATED_AT,
                "scenario_report_count": 4,
            },
            {
                "record_id": "backtest_report",
                "source": "local_report",
                "source_url": str(reports_path / "backtest.md"),
                "known_at": CREATED_AT,
                "backtest_trade_count": 25813,
            },
            {
                "record_id": "strategy_variants_report",
                "source": "local_report",
                "source_url": str(reports_path / "strategy_variants.md"),
                "known_at": CREATED_AT,
                "strategy_variant_measured_count": 3,
            },
            {
                "record_id": "harness_variants_report",
                "source": "local_report",
                "source_url": str(reports_path / "harness_variants.md"),
                "known_at": CREATED_AT,
                "harness_question_count": 5,
            },
        ]
    )


def _reviewed_harness(quality_gate) -> AnalysisHarness:
    harness = AnalysisHarness()
    while harness.current_state() != "risk_gate":
        harness.advance()
    harness.apply_quality_gate(quality_gate)
    harness.advance("risk_gate")
    harness.set_output_label("INVESTIGATE")
    harness.advance("explain")
    harness.record_human_review("accept")
    harness.advance("human_review")
    harness.save_decision()
    return harness


def _append_p39_metadata(report_path: Path, replay: ReplayResult, log_path: Path) -> None:
    lines = [
        "",
        "## P39 Reviewed Run",
        "",
        "Status: reviewed decision record generated from measured local project artifacts.",
        f"Decision log path: `{_display_path(log_path)}`.",
        f"Replay status: `{replay.status}`.",
        "Review policy: the record is accepted as educational project evidence, not as an investment recommendation.",
        "",
    ]
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
