"""CLI for measured unseen-period and regime split reporting."""

from __future__ import annotations

import argparse

from src.fundamentals_status import DEFAULT_FUNDAMENTALS_INPUT_PATH
from src.split_regime_reports import run_split_regime_from_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fundamentals",
        default=str(DEFAULT_FUNDAMENTALS_INPUT_PATH),
        help="Path to local point-in-time fundamentals CSV.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_split_regime_from_settings(fundamentals_path=args.fundamentals)
    except Exception as exc:
        print("status=error")
        print(f"error={exc}")
        return 1

    print(f"status={result.status}")
    print(f"unseen_start_date={result.unseen_start_date}")
    print(f"trades={len(result.labeled_trades)}")
    print(f"stability_rows={len(result.stability_summary)}")
    print(f"regime_rows={len(result.regime_summary)}")
    print(f"warnings={len(result.warnings)}")
    print(f"report={result.output_path}")
    return 0 if result.status == "measured" else 1


if __name__ == "__main__":
    raise SystemExit(main())
