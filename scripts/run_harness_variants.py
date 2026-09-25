"""CLI for deterministic harness variant A-E experiment."""

from __future__ import annotations

import argparse

from src.harness_variant_reports import (
    DEFAULT_HARNESS_QUESTIONS_PATH,
    run_harness_variants_from_settings,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions",
        default=str(DEFAULT_HARNESS_QUESTIONS_PATH),
        help="Path to fixed harness question CSV.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_harness_variants_from_settings(questions_path=args.questions)
    except Exception as exc:
        print("status=error")
        print(f"error={exc}")
        return 1

    best_score = result.comparison.summary["score"].max()
    best_variants = result.comparison.summary[
        result.comparison.summary["score"] == best_score
    ]["variant"].astype(str)
    print(f"status={result.status}")
    print(f"questions={result.comparison.summary['question_count'].max()}")
    print(f"variants={len(result.comparison.summary)}")
    print(f"best_variants={','.join(best_variants)}")
    print(f"report={result.output_path}")
    return 0 if result.status == "measured_deterministic" else 1


if __name__ == "__main__":
    raise SystemExit(main())
