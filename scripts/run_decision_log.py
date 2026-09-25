"""CLI for the reviewed replayable decision log workflow."""

from __future__ import annotations

from src.decision_log_reports import run_decision_log_from_settings


def main(argv: list[str] | None = None) -> int:
    _ = argv
    try:
        result = run_decision_log_from_settings()
    except Exception as exc:
        print("status=error")
        print(f"error={exc}")
        return 1

    print(f"status={result.status}")
    print(f"decision_id={result.record.decision_id}")
    print(f"review_status={result.record.review_status}")
    print(f"replay_status={result.replay.status}")
    print(f"log={result.log_path}")
    print(f"report={result.report_path}")
    return 0 if result.status == "reviewed_replay_ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
