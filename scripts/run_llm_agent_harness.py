"""Run the optional live LLM agent harness."""

from __future__ import annotations

import argparse

from src.llm_agent import run_llm_agent_harness_from_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        default="auto",
        choices=("auto", "offline", "openai", "openai_compatible", "google", "gemini"),
        help="LLM provider. auto uses live LLM only when an API key is configured.",
    )
    parser.add_argument(
        "--review-status",
        default="accept",
        choices=("accept", "modify", "reject"),
        help="Human-review status recorded for the educational harness artifact.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_llm_agent_harness_from_settings(
            provider=args.provider,
            review_status=args.review_status,
        )
    except Exception as exc:
        print("status=error")
        print(f"error={exc}")
        return 1

    print(f"status={result.status}")
    print(f"provider={result.provider}")
    print(f"model={result.model}")
    print(f"label={result.explanation.label}")
    print(f"quality_gate={result.quality_gate.gate_status}")
    print(f"replay_status={result.replay.status}")
    print(f"report={result.report_path}")
    print(f"json={result.json_path}")
    if result.warnings:
        print(f"warnings={len(result.warnings)}")
    return 0 if result.replay.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
