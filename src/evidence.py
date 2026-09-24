"""Evidence bundle and quality-gate helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.validation import (
    ANALYSIS_SAFE,
    ANALYSIS_UNSAFE,
    BLOCKING,
    WARNING,
    QualityIssue,
    QualityReport,
    validate_no_future_outcome_columns,
)


DEFAULT_SOURCE_COLUMNS = (
    "source",
    "source_url",
    "known_at",
    "date",
    "publication_timestamp",
    "download_timestamp",
)
DEFAULT_ID_COLUMNS = ("signal_id", "context_id", "record_id", "symbol")


@dataclass(frozen=True)
class EvidenceBundle:
    evidence: tuple[dict[str, object], ...]
    feature_columns: tuple[str, ...]
    source_columns: tuple[str, ...]
    evidence_hash: str


@dataclass(frozen=True)
class QualityGateResult:
    gate_status: str
    issues: tuple[QualityIssue, ...]
    evidence_hash: str | None

    @property
    def has_blocking_issues(self) -> bool:
        return any(issue.severity == BLOCKING for issue in self.issues)


class EvidenceInputError(ValueError):
    """Raised when evidence input cannot be bundled or gated."""


def build_evidence_bundle(
    records: pd.DataFrame,
    feature_columns: Iterable[str],
    source_columns: Iterable[str] = DEFAULT_SOURCE_COLUMNS,
    id_columns: Iterable[str] = DEFAULT_ID_COLUMNS,
) -> EvidenceBundle:
    """Build a committed evidence bundle from observed feature rows."""

    feature_columns = tuple(feature_columns)
    source_columns = tuple(source_columns)
    if records is None or records.empty:
        raise EvidenceInputError("evidence records are empty")
    if not feature_columns:
        raise EvidenceInputError("at least one feature column is required")

    _require_columns(records, list(feature_columns), scope="evidence records")
    available_source_columns = tuple(column for column in source_columns if column in records.columns)

    evidence: list[dict[str, object]] = []
    for index, row in records.iterrows():
        evidence_id = _evidence_id(row, id_columns, index)
        observed_features = {
            column: _sanitize(row[column])
            for column in feature_columns
            if column in records.columns and pd.notna(row[column])
        }
        sources = {
            column: _sanitize(row[column])
            for column in available_source_columns
            if pd.notna(row[column])
        }
        evidence.append(
            {
                "evidence_id": evidence_id,
                "observed_features": observed_features,
                "sources": sources,
            }
        )

    evidence_tuple = tuple(evidence)
    return EvidenceBundle(
        evidence=evidence_tuple,
        feature_columns=feature_columns,
        source_columns=source_columns,
        evidence_hash=commit_evidence_set(evidence_tuple),
    )


def commit_evidence_set(evidence: Iterable[dict[str, object]]) -> str:
    """Return a stable hash for a committed evidence set."""

    payload = json.dumps(list(evidence), sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evaluate_quality_gate(
    bundle: EvidenceBundle | None,
    quality_reports: Iterable[QualityReport] = (),
    minimum_evidence_count: int = 1,
) -> QualityGateResult:
    """Combine evidence completeness and validation reports into a gate result."""

    issues: list[QualityIssue] = []
    evidence_hash = bundle.evidence_hash if bundle is not None else None

    if bundle is None:
        issues.append(
            QualityIssue(
                severity=BLOCKING,
                code="MISSING_EVIDENCE_BUNDLE",
                message="quality gate requires an evidence bundle",
            )
        )
    else:
        issues.extend(_evidence_issues(bundle, minimum_evidence_count))
        feature_report = validate_no_future_outcome_columns(bundle.feature_columns)
        issues.extend(feature_report.issues)

    for report in quality_reports:
        issues.extend(report.issues)

    gate_status = ANALYSIS_UNSAFE if any(issue.severity == BLOCKING for issue in issues) else ANALYSIS_SAFE
    return QualityGateResult(
        gate_status=gate_status,
        issues=tuple(issues),
        evidence_hash=evidence_hash,
    )


def quality_gate_to_dict(result: QualityGateResult) -> dict[str, object]:
    return {
        "gate_status": result.gate_status,
        "evidence_hash": result.evidence_hash,
        "issues": [asdict(issue) for issue in result.issues],
    }


def write_evidence_report(result: QualityGateResult, output_path: str | Path) -> Path:
    """Write a compact markdown report for evidence and quality gate status."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Evidence Bundle And Quality Gate",
        "",
        f"Gate status: `{result.gate_status}`.",
        f"Evidence hash: `{result.evidence_hash}`." if result.evidence_hash else "Evidence hash: not available.",
        "",
    ]

    if result.issues:
        lines.extend(["## Issues", ""])
        for issue in result.issues:
            symbol = f" ({issue.symbol})" if issue.symbol else ""
            lines.append(f"- `{issue.severity}` `{issue.code}`{symbol}: {issue.message}")
        lines.append("")
    else:
        lines.extend(["No quality issues.", ""])

    lines.extend(
        [
            "Rules:",
            "- Every numerical or feature claim must be linked to observed features and source metadata.",
            "- Missing source metadata and small samples remain warnings.",
            "- Future leakage, broken history and critical date mismatches block analysis.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _evidence_issues(
    bundle: EvidenceBundle,
    minimum_evidence_count: int,
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    if minimum_evidence_count <= 0:
        raise EvidenceInputError("minimum_evidence_count must be positive")
    if len(bundle.evidence) < minimum_evidence_count:
        issues.append(
            QualityIssue(
                severity=WARNING,
                code="SMALL_EVIDENCE_SET",
                message=(
                    f"evidence bundle has {len(bundle.evidence)} rows, below "
                    f"{minimum_evidence_count}"
                ),
            )
        )

    for record in bundle.evidence:
        evidence_id = str(record["evidence_id"])
        observed_features = record.get("observed_features") or {}
        sources = record.get("sources") or {}
        if not observed_features:
            issues.append(
                QualityIssue(
                    severity=WARNING,
                    code="NO_OBSERVED_FEATURES",
                    message=f"{evidence_id} has no observed feature values",
                )
            )
        if not sources.get("source"):
            issues.append(
                QualityIssue(
                    severity=WARNING,
                    code="MISSING_SOURCE",
                    message=f"{evidence_id} has no source metadata",
                )
            )

    return issues


def _evidence_id(row: pd.Series, id_columns: Iterable[str], fallback_index: object) -> str:
    for column in id_columns:
        if column in row.index and pd.notna(row[column]) and str(row[column]).strip() != "":
            return str(row[column])
    return str(fallback_index)


def _sanitize(value):
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize(item) for item in value)
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def _require_columns(frame: pd.DataFrame, columns: list[str], scope: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise EvidenceInputError(f"{scope} missing required columns: {', '.join(missing)}")
