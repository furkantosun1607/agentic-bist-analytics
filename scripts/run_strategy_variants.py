"""CLI for measured strategy variant A-E comparison."""

from __future__ import annotations

import argparse

from src.fundamentals_status import DEFAULT_FUNDAMENTALS_INPUT_PATH
from src.news_context import DEFAULT_NEWS_CONTEXT_OUTPUT_PATH
from src.strategy_variant_reports import run_strategy_variants_from_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fundamentals",
        default=str(DEFAULT_FUNDAMENTALS_INPUT_PATH),
        help="Path to local point-in-time fundamentals CSV.",
    )
    parser.add_argument(
        "--rss-context",
        default=str(DEFAULT_NEWS_CONTEXT_OUTPUT_PATH),
        help="Path to local RSS context CSV for Variant E metadata.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_strategy_variants_from_settings(
            fundamentals_path=args.fundamentals,
            rss_context_path=args.rss_context,
        )
    except Exception as exc:
        print("status=error")
        print(f"error={exc}")
        return 1

    status_counts = result.comparison.summary["status"].value_counts().to_dict()
    print(f"status={result.status}")
    print(f"variants={len(result.comparison.summary)}")
    print(f"trades={len(result.comparison.trades)}")
    print(f"status_counts={status_counts}")
    print(f"component_signal_counts={result.component_signal_counts}")
    print(f"unavailable_components={','.join(result.unavailable_components)}")
    print(f"report={result.output_path}")
    return 0 if result.status in {"measured", "measured_partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
