"""Run Scenario 4 quarterly fundamentals/price-reaction analysis for one symbol."""

from __future__ import annotations

import argparse
import sys

from src.scenario_symbol_analysis import analyze_fundamentals_reaction_from_settings
from src.symbol_analysis import command_symbol_from_args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="+", help="Ticker query, e.g. Analyze TUPRS.IS")
    parser.add_argument("--output", help="Optional markdown output path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = analyze_fundamentals_reaction_from_settings(
            command_symbol_from_args(args.query),
            output_path=args.output,
        )
    except Exception as exc:
        print(f"fundamentals_reaction_failed={exc}", file=sys.stderr)
        return 1
    print(result.text)
    print("")
    print(f"report={result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
