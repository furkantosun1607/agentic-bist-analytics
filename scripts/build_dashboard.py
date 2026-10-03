"""Build the static project dashboard."""

from __future__ import annotations

import argparse

from src.ui_dashboard import DEFAULT_DASHBOARD_PATH, build_dashboard_from_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(DEFAULT_DASHBOARD_PATH),
        help="Output HTML path.",
    )
    args = parser.parse_args(argv)

    try:
        result = build_dashboard_from_settings(output_path=args.output)
    except Exception as exc:
        print("status=error")
        print(f"error={exc}")
        return 1

    print(f"status={result.status}")
    print(f"reports={result.report_count}")
    print(f"missing_reports={result.missing_report_count}")
    print(f"llm_status={result.llm_status}")
    print(f"output={result.output_path}")
    return 0 if result.status in {"ready", "warning"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
