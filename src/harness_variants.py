"""Harness variant comparison A-E."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


HARNESS_VARIANT_COLUMNS = (
    "variant",
    "description",
    "question_count",
    "unsupported_number_count",
    "invalid_tool_call_count",
    "evidence_complete_count",
    "replayable_count",
    "quality_gate_count",
    "human_review_count",
    "score",
    "status",
)
REQUIRED_QUESTION_COLUMNS = (
    "question_id",
    "requires_numbers",
    "requires_tools",
    "requires_state_enforcement",
    "requires_evidence",
    "requires_quality_gate",
    "requires_replay",
    "requires_human_review",
)


@dataclass(frozen=True)
class HarnessVariant:
    name: str
    description: str
    has_tools: bool
    enforces_states: bool
    has_evidence_gate: bool
    has_replay: bool
    has_human_review: bool


@dataclass(frozen=True)
class HarnessVariantComparisonResult:
    summary: pd.DataFrame
    questions: pd.DataFrame


class HarnessVariantInputError(ValueError):
    """Raised when harness variant inputs are structurally invalid."""


HARNESS_VARIANTS = (
    HarnessVariant(
        name="A",
        description="raw LLM",
        has_tools=False,
        enforces_states=False,
        has_evidence_gate=False,
        has_replay=False,
        has_human_review=False,
    ),
    HarnessVariant(
        name="B",
        description="LLM + tools",
        has_tools=True,
        enforces_states=False,
        has_evidence_gate=False,
        has_replay=False,
        has_human_review=False,
    ),
    HarnessVariant(
        name="C",
        description="tools + enforced states",
        has_tools=True,
        enforces_states=True,
        has_evidence_gate=False,
        has_replay=False,
        has_human_review=False,
    ),
    HarnessVariant(
        name="D",
        description="C + evidence/quality gate",
        has_tools=True,
        enforces_states=True,
        has_evidence_gate=True,
        has_replay=False,
        has_human_review=False,
    ),
    HarnessVariant(
        name="E",
        description="D + memory/human review",
        has_tools=True,
        enforces_states=True,
        has_evidence_gate=True,
        has_replay=True,
        has_human_review=True,
    ),
)


def compare_harness_variants(questions: pd.DataFrame) -> HarnessVariantComparisonResult:
    """Compare harness variants on the same fixed questions."""

    _validate_questions(questions)
    detailed_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for variant in HARNESS_VARIANTS:
        variant_rows = [_evaluate_question(variant, row) for _, row in questions.iterrows()]
        detailed_rows.extend(variant_rows)
        summary_rows.append(_summary_row(variant, variant_rows))

    return HarnessVariantComparisonResult(
        summary=pd.DataFrame(summary_rows).loc[:, list(HARNESS_VARIANT_COLUMNS)],
        questions=pd.DataFrame(detailed_rows),
    )


def write_harness_variants_report(
    result: HarnessVariantComparisonResult,
    output_path: str | Path,
) -> Path:
    """Write a compact markdown report for harness variant comparisons."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Harness Variant Comparison A-E",
        "",
        "Variants:",
        "- A: raw LLM",
        "- B: LLM + tools",
        "- C: tools + enforced states",
        "- D: C + evidence/quality gate",
        "- E: D + memory/human review",
        "",
    ]

    if result.summary.empty:
        lines.extend(["Status: no harness variant summary generated.", ""])
    else:
        lines.extend(["## Summary", "", result.summary.to_markdown(index=False), ""])

    lines.extend(
        [
            "Limitations:",
            "- This compares harness capabilities on fixed question requirements.",
            "- It does not execute a live LLM.",
            "- Financial strategy A-E and harness A-E are separate comparison tracks.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _evaluate_question(variant: HarnessVariant, row: pd.Series) -> dict[str, object]:
    requires_numbers = bool(row["requires_numbers"])
    requires_tools = bool(row["requires_tools"])
    requires_state_enforcement = bool(row["requires_state_enforcement"])
    requires_evidence = bool(row["requires_evidence"])
    requires_quality_gate = bool(row["requires_quality_gate"])
    requires_replay = bool(row["requires_replay"])
    requires_human_review = bool(row["requires_human_review"])

    unsupported_number = requires_numbers and not variant.has_tools
    invalid_tool_call = requires_tools and (not variant.has_tools or (
        requires_state_enforcement and not variant.enforces_states
    ))
    evidence_complete = (not requires_evidence) or variant.has_evidence_gate
    quality_gate_available = (not requires_quality_gate) or variant.has_evidence_gate
    replayable = (not requires_replay) or variant.has_replay
    human_review_available = (not requires_human_review) or variant.has_human_review

    passed = (
        not unsupported_number
        and not invalid_tool_call
        and evidence_complete
        and quality_gate_available
        and replayable
        and human_review_available
    )

    return {
        "variant": variant.name,
        "description": variant.description,
        "question_id": str(row["question_id"]),
        "unsupported_number": unsupported_number,
        "invalid_tool_call": invalid_tool_call,
        "evidence_complete": evidence_complete,
        "quality_gate_available": quality_gate_available,
        "replayable": replayable,
        "human_review_available": human_review_available,
        "passed": passed,
    }


def _summary_row(variant: HarnessVariant, rows: list[dict[str, object]]) -> dict[str, object]:
    question_count = len(rows)
    passed_count = sum(1 for row in rows if row["passed"])
    score = passed_count / question_count if question_count else 0

    return {
        "variant": variant.name,
        "description": variant.description,
        "question_count": question_count,
        "unsupported_number_count": sum(1 for row in rows if row["unsupported_number"]),
        "invalid_tool_call_count": sum(1 for row in rows if row["invalid_tool_call"]),
        "evidence_complete_count": sum(1 for row in rows if row["evidence_complete"]),
        "replayable_count": sum(1 for row in rows if row["replayable"]),
        "quality_gate_count": sum(1 for row in rows if row["quality_gate_available"]),
        "human_review_count": sum(1 for row in rows if row["human_review_available"]),
        "score": score,
        "status": "ok" if score == 1 else "limited",
    }


def _validate_questions(questions: pd.DataFrame) -> None:
    if questions is None or questions.empty:
        raise HarnessVariantInputError("questions are empty")
    missing = [column for column in REQUIRED_QUESTION_COLUMNS if column not in questions.columns]
    if missing:
        raise HarnessVariantInputError(f"questions missing required columns: {', '.join(missing)}")
