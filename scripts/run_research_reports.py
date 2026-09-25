"""Run all four required research reports from local cache artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.research_reports import run_research_reports_from_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local cached research reports.")
    parser.add_argument(
        "--fundamentals",
        default="data/fundamentals/fundamentals.csv",
        help="Path to local fundamentals CSV.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = run_research_reports_from_settings(fundamentals_path=Path(args.fundamentals))
    except Exception as exc:
        print(f"research_reports_failed={exc}")
        return 1

    print(f"reports={len(result.reports)}")
    print(f"missing_price_symbols={len(result.missing_price_symbols)}")
    print(f"generated_event_rows={result.generated_event_rows}")
    print(f"fundamentals_rows={result.fundamentals_rows}")
    for report in result.reports:
        print(
            f"{report.report_name}={report.status}: "
            f"observations={report.observation_rows}, errors={len(report.errors)}"
        )
    return 0 if all(report.status == "measured" for report in result.reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
