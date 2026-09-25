"""Measured deterministic harness variant experiment runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.harness_variants import (
    HarnessVariantComparisonResult,
    compare_harness_variants,
    write_harness_variants_report,
)
from src.settings import PROJECT_ROOT, Settings, load_settings


DEFAULT_HARNESS_QUESTIONS_PATH = PROJECT_ROOT / "config" / "harness_questions.csv"
BOOLEAN_QUESTION_COLUMNS = (
    "requires_numbers",
    "requires_tools",
    "requires_state_enforcement",
    "requires_evidence",
    "requires_quality_gate",
    "requires_replay",
    "requires_human_review",
)


@dataclass(frozen=True)
class HarnessVariantRunResult:
    status: str
    comparison: HarnessVariantComparisonResult
    questions_path: Path
    output_path: Path


def run_harness_variants_from_settings(
    settings: Settings | None = None,
    questions_path: str | Path = DEFAULT_HARNESS_QUESTIONS_PATH,
) -> HarnessVariantRunResult:
    """Run P38 harness variants from the configured reports directory."""

    active_settings = settings or load_settings()
    return run_harness_variants(
        questions_path=questions_path,
        reports_dir=active_settings.paths.reports_dir,
    )


def run_harness_variants(
    questions_path: str | Path = DEFAULT_HARNESS_QUESTIONS_PATH,
    reports_dir: str | Path = PROJECT_ROOT / "reports",
) -> HarnessVariantRunResult:
    """Load the fixed question fixture, compare harness variants and write report."""

    path = Path(questions_path)
    questions = load_harness_questions(path)
    comparison = compare_harness_variants(questions)
    output_path = write_harness_variants_report(
        comparison,
        Path(reports_dir) / "harness_variants.md",
    )
    result = HarnessVariantRunResult(
        status=_run_status(comparison),
        comparison=comparison,
        questions_path=path,
        output_path=output_path,
    )
    _append_harness_variant_metadata(result)
    return result


def load_harness_questions(path: str | Path) -> pd.DataFrame:
    """Load fixed harness questions and normalize boolean requirement fields."""

    frame = pd.read_csv(path)
    for column in BOOLEAN_QUESTION_COLUMNS:
        if column in frame.columns:
            frame[column] = frame[column].map(_parse_bool)
    return frame


def _append_harness_variant_metadata(result: HarnessVariantRunResult) -> None:
    lines = [
        "",
        "## Deterministic Experiment Run",
        "",
        f"Status: {result.status}.",
        f"Fixed question set: `{_display_path(result.questions_path)}`.",
        "Execution policy: this run does not call a live LLM; it deterministically scores harness capabilities against fixed question requirements.",
        "",
        "## Question Outcomes",
        "",
    ]
    if result.comparison.questions.empty:
        lines.extend(["No question outcomes generated.", ""])
    else:
        outcome_summary = (
            result.comparison.questions.groupby(["variant", "passed"], dropna=False)
            .agg(question_count=("question_id", "count"))
            .reset_index()
            .sort_values(["variant", "passed"])
        )
        lines.extend([outcome_summary.to_markdown(index=False), ""])

    lines.extend(
        [
            "Measured-run limitations:",
            "- This is a deterministic harness capability experiment, not a live LLM benchmark.",
            "- It measures whether a harness design can support required controls; it does not judge answer prose quality.",
            "- Financial strategy A-E and harness A-E are separate comparison tracks.",
            "",
        ]
    )
    with result.output_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def _run_status(comparison: HarnessVariantComparisonResult) -> str:
    if comparison.summary.empty:
        return "inconclusive"
    if "ok" in set(comparison.summary["status"].astype(str)):
        return "measured_deterministic"
    return "inconclusive"


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
