"""CLI for the measured backtest and risk report workflow."""

from __future__ import annotations

import argparse

from src.backtest_reports import run_backtests_from_settings
from src.fundamentals_status import DEFAULT_FUNDAMENTALS_INPUT_PATH


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fundamentals",
        default=str(DEFAULT_FUNDAMENTALS_INPUT_PATH),
        help="Path to local point-in-time fundamentals CSV.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_backtests_from_settings(fundamentals_path=args.fundamentals)
    except Exception as exc:
        print(f"status=error")
        print(f"error={exc}")
        return 1

    ok_trades = (
        int((result.backtest.trades["status"] == "ok").sum())
        if not result.backtest.trades.empty and "status" in result.backtest.trades.columns
        else 0
    )
    print(f"status={result.status}")
    print(f"signals={len(result.signals)}")
    print(f"trades={len(result.backtest.trades)}")
    print(f"ok_trades={ok_trades}")
    print(f"missing_price_symbols={len(result.missing_price_symbols)}")
    print(f"assembly_warnings={len(result.errors)}")
    print(f"report={result.output_path}")
    return 0 if result.status == "measured" else 1


if __name__ == "__main__":
    raise SystemExit(main())
