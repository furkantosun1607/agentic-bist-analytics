import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.data import normalize_price_frame, write_price_cache
from src.market_audit import audit_market_cache, write_market_cache_audit_report


def raw_prices(rows=25):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": [100 + index for index in range(rows)],
            "High": [101 + index for index in range(rows)],
            "Low": [99 + index for index in range(rows)],
            "Close": [100.5 + index for index in range(rows)],
            "Adj Close": [100.4 + index for index in range(rows)],
            "Volume": [1000 + index for index in range(rows)],
        }
    )


class MarketAuditTests(unittest.TestCase):
    def test_audit_market_cache_reports_pass_and_missing_symbols(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            prices = normalize_price_frame(
                symbol="AAA.IS",
                raw_prices=raw_prices(),
                source="unit_test",
                download_timestamp="2026-09-24T10:00:00+00:00",
            )
            write_price_cache(prices, cache_dir, "AAA.IS")

            rows = audit_market_cache(
                symbols=["AAA.IS", "MISSING.IS"],
                benchmark_symbol="MISSING.IS",
                cache_dir=cache_dir,
                warn_on_small_sample_below=20,
            )
            by_symbol = {row.symbol: row for row in rows}

            self.assertEqual("pass", by_symbol["AAA.IS"].status)
            self.assertEqual(25, by_symbol["AAA.IS"].row_count)
            self.assertEqual("2024-01-01", by_symbol["AAA.IS"].start_date)
            self.assertEqual("benchmark", by_symbol["MISSING.IS"].role)
            self.assertEqual("error", by_symbol["MISSING.IS"].status)
            self.assertIn("CACHE_FILE_MISSING", by_symbol["MISSING.IS"].issues)

    def test_audit_market_cache_marks_small_sample_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            prices = normalize_price_frame(
                symbol="AAA.IS",
                raw_prices=raw_prices(rows=5),
                source="unit_test",
                download_timestamp="2026-09-24T10:00:00+00:00",
            )
            write_price_cache(prices, cache_dir, "AAA.IS")

            rows = audit_market_cache(
                symbols=["AAA.IS"],
                benchmark_symbol="XU100.IS",
                cache_dir=cache_dir,
                warn_on_small_sample_below=20,
            )

            self.assertEqual("warning", rows[0].status)
            self.assertIn("SMALL_SAMPLE", rows[0].issues)

    def test_write_market_cache_audit_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "market_cache_audit.md"
            rows = audit_market_cache(
                symbols=["MISSING.IS"],
                benchmark_symbol="MISSING.IS",
                cache_dir=Path(tmpdir) / "cache",
                warn_on_small_sample_below=20,
            )

            written = write_market_cache_audit_report(
                rows=rows,
                output_path=output,
                cache_dir=Path(tmpdir) / "cache",
                adjusted_price_policy="use_adjusted_close_when_available",
                configured_start_date="2021-01-01",
                configured_end_date=None,
            )

            text = written.read_text(encoding="utf-8")
            self.assertIn("# Market Cache Audit", text)
            self.assertIn("CACHE_FILE_MISSING", text)


if __name__ == "__main__":
    unittest.main()
