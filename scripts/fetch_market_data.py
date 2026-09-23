"""Fetch configured market data into the local cache."""

from __future__ import annotations

from src.data import fetch_market_data, load_universe, write_missing_symbols_report
from src.settings import load_settings


def main() -> int:
    settings = load_settings()
    universe = load_universe(settings.paths.universe)
    symbols = [member.yahoo_symbol for member in universe]
    result = fetch_market_data(
        symbols=symbols,
        benchmark_symbol=settings.market_data.benchmark_symbol,
        start_date=settings.market_data.start_date,
        end_date=settings.market_data.end_date,
        cache_dir=settings.paths.cache_dir,
        source=settings.market_data.price_source,
    )

    write_missing_symbols_report(result.missing_symbols, settings.paths.reports_dir)
    print(f"cached_symbols={len(result.prices)}")
    print(f"missing_symbols={len(result.missing_symbols)}")
    print(f"cache_dir={result.cache_dir}")
    return 1 if result.missing_symbols else 0


if __name__ == "__main__":
    raise SystemExit(main())
