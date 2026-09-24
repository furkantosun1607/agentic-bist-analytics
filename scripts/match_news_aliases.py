"""Match deterministic ticker, sector, and macro aliases against RSS news."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.news_aliases import match_news_cache, summarize_alias_matches


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Match configured aliases against RSS news.")
    parser.add_argument(
        "--input",
        default="data/rss/news.jsonl",
        help="Path to normalized RSS JSONL cache.",
    )
    parser.add_argument(
        "--aliases",
        default="config/news_aliases.csv",
        help="Path to news aliases CSV.",
    )
    parser.add_argument(
        "--output",
        default="data/rss/news_matched.jsonl",
        help="Path for alias-enriched RSS JSONL cache.",
    )
    parser.add_argument(
        "--report",
        default="reports/news_alias_matches.md",
        help="Path for alias match coverage report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        matched = match_news_cache(
            input_path=Path(args.input),
            aliases_path=Path(args.aliases),
            output_path=Path(args.output),
            report_path=Path(args.report),
        )
    except Exception as exc:
        print(f"news_alias_match_failed={exc}")
        return 1

    summary = summarize_alias_matches(matched)
    print(f"total_items={summary.total_items}")
    print(f"matched_items={summary.matched_items}")
    print(f"unmatched_items={summary.unmatched_items}")
    print(f"output={args.output}")
    print(f"report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
