import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.context import MACRO_INDICATORS
from src.macro_context_fetch import (
    STATIC_MACRO_RECORDS,
    build_fx_context_rows,
    fetch_macro_context,
)


class FakeFxProvider:
    def __init__(self, fail_symbol=None):
        self.fail_symbol = fail_symbol
        self.requests = []

    def download(self, symbol, start, end):
        self.requests.append((symbol, start, end))
        if symbol == self.fail_symbol:
            raise RuntimeError("fx provider unavailable")
        return pd.DataFrame(
            {
                "Date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
                "Close": [30.0, 30.5] if symbol == "USDTRY=X" else [33.0, 33.5],
            }
        )


class MacroContextFetchTest(unittest.TestCase):
    def test_build_fx_context_rows_uses_next_morning_publication_time(self):
        raw = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2024-01-02"]),
                "Close": [30.0],
            }
        )

        rows = build_fx_context_rows(
            raw_rates=raw,
            indicator="usd_try",
            symbol="USDTRY=X",
            unit="TRY per USD",
            download_timestamp="2026-09-24T10:00:00+00:00",
        )

        self.assertEqual(1, len(rows))
        self.assertEqual("macro-usd_try-2024-01-02", rows[0]["context_id"])
        self.assertEqual("2024-01-03T09:00:00+03:00", rows[0]["publication_timestamp"])
        self.assertEqual("yahoo_finance_fx", rows[0]["source"])

    def test_build_fx_context_rows_skips_rows_not_public_by_download_time(self):
        raw = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2024-01-02"]),
                "Close": [30.0],
            }
        )

        rows = build_fx_context_rows(
            raw_rates=raw,
            indicator="usd_try",
            symbol="USDTRY=X",
            unit="TRY per USD",
            download_timestamp="2024-01-02T12:00:00+00:00",
        )

        self.assertEqual([], rows)

    def test_fetch_macro_context_writes_fx_and_static_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "macro_context.csv"
            report_path = Path(tmpdir) / "macro_context_fetch_status.md"

            result = fetch_macro_context(
                output_path=output_path,
                report_path=report_path,
                provider=FakeFxProvider(),
                start_date="2024-01-01",
                end_date="2024-01-05",
                download_timestamp="2026-09-24T10:00:00+00:00",
            )

            self.assertEqual(2 * 2 + len(STATIC_MACRO_RECORDS), len(result.records))
            self.assertEqual((), result.errors)
            self.assertTrue(output_path.exists())
            self.assertTrue(report_path.exists())
            self.assertEqual(set(MACRO_INDICATORS), set(result.records["indicator"]))
            self.assertIn("static_curated_macro_records", report_path.read_text(encoding="utf-8"))

    def test_fetch_macro_context_preserves_fx_errors_but_keeps_static_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = fetch_macro_context(
                output_path=Path(tmpdir) / "macro_context.csv",
                report_path=Path(tmpdir) / "macro_context_fetch_status.md",
                provider=FakeFxProvider(fail_symbol="EURTRY=X"),
                download_timestamp="2026-09-24T10:00:00+00:00",
            )

            self.assertEqual(1, len(result.errors))
            self.assertIn("EURTRY=X", result.errors[0].source)
            self.assertIn("usd_try", set(result.records["indicator"]))
            self.assertIn("fed_policy_rate", set(result.records["indicator"]))


if __name__ == "__main__":
    unittest.main()
