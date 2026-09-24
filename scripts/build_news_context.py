"""Build decision-time safe RSS news context summaries."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from src.news_context import build_news_context_from_cache


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build RSS news context summaries.")
    parser.add_argument(
        "--input",
        default="data/rss/news_matched.jsonl",
        help="Path to alias-enriched RSS JSONL cache.",
    )
    parser.add_argument(
        "--output",
        default="data/rss/news_context.csv",
        help="Path for RSS news context CSV.",
    )
    parser.add_argument(
        "--report",
        default="reports/context_sources.md",
        help="Path for context sources report.",
    )
    parser.add_argument(
        "--decision-timestamp",
        default=datetime.now(UTC).isoformat(),
        help="Historical decision timestamp. Defaults to current UTC time.",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=7,
        help="Lookback window in days.",
    )
    parser.add_argument(
        "--universe",
        default="config/universe.csv",
        help="Path to fixed universe CSV.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = build_news_context_from_cache(
            input_path=Path(args.input),
            output_path=Path(args.output),
            report_path=Path(args.report),
            decision_timestamp=args.decision_timestamp,
            lookback_days=args.lookback_days,
            universe_path=Path(args.universe),
        )
    except Exception as exc:
        print(f"news_context_failed={exc}")
        return 1

    active_rows = [row for row in result.rows if row.news_count > 0]
    print(f"context_rows={len(result.rows)}")
    print(f"active_context_rows={len(active_rows)}")
    print(f"output={result.output_path}")
    print(f"report={result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
