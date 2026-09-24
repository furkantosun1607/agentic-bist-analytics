"""Normalize and deduplicate raw RSS news cache."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.rss_news import (
    load_rss_fetch_status_report,
    load_rss_sources,
    normalize_rss_news_cache,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize raw RSS news cache.")
    parser.add_argument(
        "--input",
        default="data/rss/news_raw.jsonl",
        help="Path to raw RSS JSONL cache.",
    )
    parser.add_argument(
        "--output",
        default="data/rss/news.jsonl",
        help="Path for normalized RSS JSONL cache.",
    )
    parser.add_argument(
        "--sources",
        default="config/rss_sources.yaml",
        help="Path to RSS source configuration YAML.",
    )
    parser.add_argument(
        "--fetch-report",
        default="reports/rss_fetch_status.md",
        help="Path to source-level fetch status report.",
    )
    parser.add_argument(
        "--health-report",
        default="reports/rss_source_health.md",
        help="Path for normalized source health report.",
    )
    parser.add_argument(
        "--stale-after-hours",
        type=int,
        default=24,
        help="Mark source stale when latest published item is older than this many hours.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = normalize_rss_news_cache(
            raw_path=Path(args.input),
            output_path=Path(args.output),
            report_path=Path(args.health_report),
            sources=load_rss_sources(Path(args.sources)),
            fetch_statuses=load_rss_fetch_status_report(Path(args.fetch_report)),
            stale_after_hours=args.stale_after_hours,
        )
    except Exception as exc:
        print(f"rss_normalize_failed={exc}")
        return 1

    for health in result.source_health:
        print(
            f"{health.source_id}={health.status}: raw={health.raw_count}; "
            f"normalized={health.normalized_count}; duplicates={health.duplicate_count}; "
            f"{health.detail}"
        )
    print(f"normalized_items={len(result.items)}")
    print(f"output={result.output_path}")
    print(f"health_report={result.report_path}")
    return 0 if result.items else 1


if __name__ == "__main__":
    raise SystemExit(main())
