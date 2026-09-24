"""Fetch configured RSS news sources into the local raw news cache."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.rss_news import fetch_rss_news, load_rss_sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch configured RSS news sources.")
    parser.add_argument(
        "--sources",
        default="config/rss_sources.yaml",
        help="Path to RSS source configuration YAML.",
    )
    parser.add_argument(
        "--output",
        default="data/rss/news_raw.jsonl",
        help="Path for raw RSS JSONL cache output.",
    )
    parser.add_argument(
        "--report",
        default="reports/rss_fetch_status.md",
        help="Path for source-level fetch status report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        sources = load_rss_sources(Path(args.sources))
        result = fetch_rss_news(
            sources=sources,
            output_path=Path(args.output),
            report_path=Path(args.report),
        )
    except Exception as exc:
        print(f"rss_fetch_failed={exc}")
        return 1

    for status in result.statuses:
        print(
            f"{status.source_id}={status.status}: "
            f"items={status.item_count}; {status.detail}"
        )
    print(f"cached_items={len(result.items)}")
    print(f"output={result.output_path}")
    print(f"report={result.report_path}")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
