"""Audit local fundamentals import readiness."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.fundamentals_status import audit_fundamentals_import


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit fundamentals import readiness.")
    parser.add_argument(
        "--input",
        default="data/fundamentals/fundamentals.csv",
        help="Path to local fundamentals CSV export.",
    )
    parser.add_argument(
        "--output",
        default="reports/fundamentals_import_status.md",
        help="Path for fundamentals import status report.",
    )
    parser.add_argument(
        "--decision-timestamp",
        default=None,
        help="Optional point-in-time validation decision timestamp.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = audit_fundamentals_import(
            input_path=Path(args.input),
            output_path=Path(args.output),
            decision_timestamp=args.decision_timestamp,
        )
    except Exception as exc:
        print(f"fundamentals_audit_failed={exc}")
        return 1

    print(f"status={result.status}")
    print(f"valid_rows={result.valid_rows}")
    print(f"import_errors={result.error_count}")
    print(f"universe_coverage={result.universe_coverage}")
    print(f"report={result.report_path}")
    return 0 if result.status.startswith("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
