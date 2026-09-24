"""Offline classroom demo command."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.demo import run_offline_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the offline classroom demo.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run without live data source calls. This is the only supported demo mode.",
    )
    parser.add_argument(
        "--settings",
        default="config/settings.yaml",
        help="Path to the project settings YAML.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path for the generated demo summary markdown.",
    )
    parser.add_argument(
        "--strict-cache",
        action="store_true",
        help="Fail when cached market files are not present.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.offline:
        parser.error("only --offline mode is supported")

    try:
        result = run_offline_demo(
            settings_path=Path(args.settings),
            output_path=Path(args.output) if args.output else None,
            strict_cache=args.strict_cache,
        )
    except Exception as exc:
        print(f"demo_failed={exc}")
        return 1

    for check in result.checks:
        print(f"{check.name}={check.status}: {check.detail}")
    print(f"summary={result.summary_path}")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
