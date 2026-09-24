"""Audit local market cache coverage and quality."""

from __future__ import annotations

from src.market_audit import audit_market_cache_from_settings


def main() -> int:
    try:
        result = audit_market_cache_from_settings()
    except Exception as exc:
        print(f"market_cache_audit_failed={exc}")
        return 1

    print(f"expected_symbols={result.expected_count}")
    print(f"cached_symbols={result.cached_count}")
    print(f"pass={result.pass_count}")
    print(f"warning={result.warning_count}")
    print(f"error={result.error_count}")
    print(f"report={result.output_path}")
    return 1 if result.error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
