"""Audit local macro context import readiness."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.macro_context_status import audit_macro_context


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit macro context import readiness.")
    parser.add_argument(
        "--input",
        default="data/macro/macro_context.csv",
        help="Path to local macro context CSV export.",
    )
    parser.add_argument(
        "--output",
        default="reports/macro_context_status.md",
        help="Path for macro context status report.",
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
        result = audit_macro_context(
            input_path=Path(args.input),
            output_path=Path(args.output),
            decision_timestamp=args.decision_timestamp,
        )
    except Exception as exc:
        print(f"macro_context_audit_failed={exc}")
        return 1

    print(f"status={result.status}")
    print(f"valid_macro_rows={result.valid_macro_rows}")
    print(f"import_errors={result.import_errors}")
    print(f"missing_indicators={len(result.missing_indicators)}")
    print(f"report={result.report_path}")
    return 0 if result.status.startswith("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
