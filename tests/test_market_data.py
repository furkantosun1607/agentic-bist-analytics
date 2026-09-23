import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.data import (
    PRICE_CACHE_COLUMNS,
    MissingSymbol,
    fetch_market_data,
    normalize_price_frame,
    price_cache_path,
    read_price_cache,
    write_missing_symbols_report,
)
from src.settings import load_settings


class FakePriceProvider:
    def __init__(self):
        self.requests = []

    def download(self, symbol, start, end):
        self.requests.append((symbol, start, end))
        if symbol == "MISSING.IS":
            return pd.DataFrame()

        return pd.DataFrame(
            {
                "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
                "Open": [10.0, 10.5],
                "High": [10.8, 10.9],
                "Low": [9.8, 10.1],
                "Close": [10.4, 10.7],
                "Adj Close": [10.2, 10.6],
                "Volume": [1000, 1200],
            }
        )


class MarketDataTest(unittest.TestCase):
    def test_normalize_price_frame_adds_source_and_timestamp_metadata(self):
        raw = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2024-01-02"]),
                "Open": [10.0],
                "High": [10.5],
                "Low": [9.9],
                "Close": [10.1],
                "Adj Close": [10.0],
                "Volume": [100],
            }
        )

        normalized = normalize_price_frame(
            symbol="ASELS.IS",
            raw_prices=raw,
            source="test_source",
            download_timestamp="2026-09-23T00:00:00+00:00",
        )

        self.assertEqual(list(PRICE_CACHE_COLUMNS), list(normalized.columns))
        self.assertEqual("ASELS.IS", normalized.loc[0, "symbol"])
        self.assertEqual("2024-01-02", normalized.loc[0, "date"])
        self.assertEqual("test_source", normalized.loc[0, "source"])
        self.assertEqual(
            "2026-09-23T00:00:00+00:00",
            normalized.loc[0, "download_timestamp"],
        )

    def test_fetch_market_data_caches_symbols_and_benchmark(self):
        provider = FakePriceProvider()
        settings = load_settings()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = fetch_market_data(
                symbols=["ASELS.IS"],
                benchmark_symbol=settings.market_data.benchmark_symbol,
                start_date=settings.market_data.start_date,
                end_date=settings.market_data.end_date,
                cache_dir=tmpdir,
                provider=provider,
                download_timestamp="2026-09-23T00:00:00+00:00",
            )

            self.assertEqual(set(result.prices), {"ASELS.IS", "XU100.IS"})
            self.assertEqual((), result.missing_symbols)
            self.assertTrue(price_cache_path(Path(tmpdir), "ASELS.IS").exists())
            self.assertTrue(price_cache_path(Path(tmpdir), "XU100.IS").exists())

            cached = read_price_cache(tmpdir, "ASELS.IS")
            self.assertEqual(2, len(cached))
            self.assertEqual("yahoo_finance", cached.loc[0, "source"])

    def test_fetch_market_data_reports_missing_symbols(self):
        provider = FakePriceProvider()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = fetch_market_data(
                symbols=["MISSING.IS"],
                benchmark_symbol="XU100.IS",
                start_date="2024-01-01",
                end_date=None,
                cache_dir=tmpdir,
                provider=provider,
                download_timestamp="2026-09-23T00:00:00+00:00",
            )

            self.assertEqual(["XU100.IS"], list(result.prices))
            self.assertEqual(1, len(result.missing_symbols))
            self.assertEqual("MISSING.IS", result.missing_symbols[0].symbol)
            self.assertIn("no price rows", result.missing_symbols[0].reason)

    def test_write_missing_symbols_report(self):
        missing = [MissingSymbol(symbol="MISSING.IS", reason="no price rows returned")]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = write_missing_symbols_report(missing, tmpdir)

            self.assertTrue(output_path.exists())
            self.assertEqual(
                ["symbol,reason", "MISSING.IS,no price rows returned"],
                output_path.read_text(encoding="utf-8").strip().splitlines(),
            )


if __name__ == "__main__":
    unittest.main()
