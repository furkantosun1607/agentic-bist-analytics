"""Generate local macro context CSV from yfinance FX and static curated records."""

from __future__ import annotations

import argparse

from src.macro_context_fetch import fetch_macro_context
from src.settings import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate local macro context CSV.")
    parser.add_argument(
        "--output",
        default="data/macro/macro_context.csv",
        help="Output macro context CSV path.",
    )
    parser.add_argument(
        "--start",
        default="2024-01-01",
        help="Start date for yfinance FX history.",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Optional end date for yfinance FX history.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = load_settings()

    try:
        result = fetch_macro_context(
            output_path=args.output,
            start_date=args.start,
            end_date=args.end,
            timezone=settings.project.timezone,
        )
    except Exception as exc:
        print(f"macro_context_fetch_failed={exc}")
        return 1

    print(f"rows={len(result.records)}")
    print(f"errors={len(result.errors)}")
    print(f"output={result.output_path}")
    print(f"report={result.report_path}")
    return 0 if len(result.records) and not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
