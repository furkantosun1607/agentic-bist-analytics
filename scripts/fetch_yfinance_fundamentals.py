"""Fetch Yahoo Finance quarterly fundamentals into the local fundamentals CSV."""

from __future__ import annotations

import argparse

from src.data import load_universe
from src.settings import load_settings
from src.yfinance_fundamentals import fetch_yfinance_fundamentals


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch yfinance quarterly fundamentals.")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output CSV path. Defaults to config fundamentals.output_path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = load_settings()
    universe = load_universe(settings.paths.universe)

    try:
        result = fetch_yfinance_fundamentals(
            universe=universe,
            output_path=args.output or settings.fundamentals.output_path,
            synthetic_lag_days=settings.fundamentals.synthetic_disclosure_lag_days,
            synthetic_disclosure_time=settings.fundamentals.synthetic_disclosure_time,
            timezone=settings.project.timezone,
        )
    except Exception as exc:
        print(f"fundamentals_fetch_failed={exc}")
        return 1

    print(f"rows={len(result.records)}")
    print(f"errors={len(result.errors)}")
    print(f"output={result.output_path}")
    print(f"report={result.report_path}")
    return 0 if len(result.records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
