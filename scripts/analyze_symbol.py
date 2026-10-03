"""Print a one-screen educational analysis for a fixed-universe BIST symbol."""

from __future__ import annotations

import argparse
import sys

from src.symbol_analysis import analyze_symbol_from_settings, command_symbol_from_args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "query",
        nargs="+",
        help="Ticker query, e.g. ASELS.IS, ASELS, or classroom-style Analyze ASELS.IS.",
    )
    parser.add_argument(
        "--output",
        help="Optional markdown output path. Defaults to reports/symbol_analysis/<symbol>.md.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        symbol = command_symbol_from_args(args.query)
        result = analyze_symbol_from_settings(symbol, output_path=args.output)
    except Exception as exc:
        print(f"symbol_analysis_failed={exc}", file=sys.stderr)
        return 1

    print(result.text)
    print("")
    print(f"report={result.report_path}")
    print(f"label={result.label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
