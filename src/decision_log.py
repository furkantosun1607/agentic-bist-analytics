"""Replayable human-reviewed decision log helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from src.evidence import QualityGateResult, quality_gate_to_dict
from src.harness import AnalysisHarness


DECISION_LOG_SCHEMA_VERSION = "1.0"
ALLOWED_REVIEW_STATUS = ("accept", "modify", "reject")


@dataclass(frozen=True)
class DecisionRecord:
    schema_version: str
    decision_id: str
    created_at: str
    output_label: str
    review_status: str
    reviewer: str
    review_notes: str
    harness_snapshot: dict[str, object]
    inputs: dict[str, object]
    tool_outputs: dict[str, object]
    evidence_hash: str
    quality_gate: dict[str, object]
    record_hash: str


@dataclass(frozen=True)
class ReplayResult:
    status: str
    decision_id: str
    messages: tuple[str, ...]


class DecisionLogError(ValueError):
    """Raised when a decision log cannot be created or replayed."""


def create_decision_record(
    decision_id: str,
    harness: AnalysisHarness,
    inputs: dict[str, object],
    tool_outputs: dict[str, object],
    quality_gate: QualityGateResult,
    reviewer: str,
    review_notes: str = "",
    created_at: str | None = None,
) -> DecisionRecord:
    """Create a replayable decision record from harness and evidence state."""

    _validate_harness_ready(harness)
    review_status = str(harness.review_status or "").lower()
    if review_status not in ALLOWED_REVIEW_STATUS:
        raise DecisionLogError(f"review_status must be one of {', '.join(ALLOWED_REVIEW_STATUS)}")
    if not reviewer.strip():
        raise DecisionLogError("reviewer is required")
    if not quality_gate.evidence_hash:
        raise DecisionLogError("quality gate must include an evidence hash")

    base = {
        "schema_version": DECISION_LOG_SCHEMA_VERSION,
        "decision_id": decision_id,
        "created_at": created_at or datetime.now(UTC).isoformat(),
        "output_label": str(harness.output_label),
        "review_status": review_status,
        "reviewer": reviewer.strip(),
        "review_notes": review_notes,
        "harness_snapshot": harness.snapshot(),
        "inputs": _sanitize(inputs),
        "tool_outputs": _sanitize(tool_outputs),
        "evidence_hash": quality_gate.evidence_hash,
        "quality_gate": quality_gate_to_dict(quality_gate),
    }
    record_hash = _stable_hash(base)
    return DecisionRecord(record_hash=record_hash, **base)


def append_decision_record(record: DecisionRecord, log_dir: str | Path) -> Path:
    """Append one decision record to the JSONL decision log."""

    output_dir = Path(log_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "decisions.jsonl"
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), sort_keys=True, default=str))
        handle.write("\n")
    return output_path


def load_decision_records(path: str | Path) -> list[DecisionRecord]:
    """Load JSONL decision records."""

    records: list[DecisionRecord] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                records.append(_decision_record_from_dict(raw))
            except Exception as exc:
                raise DecisionLogError(f"invalid decision log line {line_number}: {exc}") from exc
    return records


def replay_decision_record(record: DecisionRecord) -> ReplayResult:
    """Replay-check record integrity and required artifacts."""

    messages: list[str] = []
    recomputed_hash = _stable_hash(_record_without_hash(record))
    if recomputed_hash != record.record_hash:
        messages.append("record_hash mismatch")

    gate_hash = record.quality_gate.get("evidence_hash")
    if gate_hash != record.evidence_hash:
        messages.append("quality_gate evidence_hash does not match record evidence_hash")

    snapshot = record.harness_snapshot
    if snapshot.get("output_label") != record.output_label:
        messages.append("harness output_label does not match decision output_label")
    if snapshot.get("review_status") != record.review_status:
        messages.append("harness review_status does not match decision review_status")

    required_sections = {
        "inputs": record.inputs,
        "tool_outputs": record.tool_outputs,
        "quality_gate": record.quality_gate,
    }
    for section, value in required_sections.items():
        if not value:
            messages.append(f"{section} is empty")

    return ReplayResult(
        status="ok" if not messages else "error",
        decision_id=record.decision_id,
        messages=tuple(messages),
    )


def write_decision_log_report(
    records: Iterable[DecisionRecord],
    output_path: str | Path,
) -> Path:
    """Write a compact markdown report for decision log status."""

    records = list(records)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Human Review And Replayable Decision Log",
        "",
        f"Decision records: {len(records)}.",
        "",
    ]
    if records:
        lines.extend(["## Records", ""])
        for record in records:
            lines.append(
                f"- `{record.decision_id}`: label `{record.output_label}`, "
                f"review `{record.review_status}`, gate `{record.quality_gate.get('gate_status')}`"
            )
        lines.append("")
    else:
        lines.extend(["No reviewed decisions have been logged yet.", ""])

    lines.extend(
        [
            "Rules:",
            "- Decisions require an output label, human review and evidence hash.",
            "- JSONL records include inputs, tool outputs, harness snapshot and quality gate result.",
            "- Replay checks record integrity and evidence-hash consistency.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _validate_harness_ready(harness: AnalysisHarness) -> None:
    if harness.output_label is None:
        raise DecisionLogError("harness output_label is required")
    if harness.review_status is None:
        raise DecisionLogError("harness review_status is required")
    if not harness.saved:
        raise DecisionLogError("harness decision must be saved before logging")


def _decision_record_from_dict(raw: dict[str, object]) -> DecisionRecord:
    required = set(DecisionRecord.__dataclass_fields__)
    missing = sorted(required - set(raw))
    if missing:
        raise DecisionLogError(f"missing fields: {', '.join(missing)}")
    return DecisionRecord(**{field: raw[field] for field in DecisionRecord.__dataclass_fields__})


def _record_without_hash(record: DecisionRecord) -> dict[str, object]:
    payload = asdict(record)
    payload.pop("record_hash", None)
    return payload


def _stable_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(_sanitize(payload), sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _sanitize(value):
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value
