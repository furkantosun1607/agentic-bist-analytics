import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.data import UniverseMember
from src.yfinance_fundamentals import (
    YFinanceStatementBundle,
    build_yfinance_fundamentals_rows,
    fetch_yfinance_fundamentals,
    synthetic_disclosure_timestamp,
)


class FakeFundamentalsProvider:
    def fetch(self, symbol):
        if symbol == "MISSING.IS":
            raise RuntimeError("provider unavailable")

        columns = pd.to_datetime(["2024-03-31", "2023-12-31"])
        return YFinanceStatementBundle(
            income=pd.DataFrame(
                {
                    columns[0]: {
                        "Total Revenue": 500.0,
                        "Gross Profit": 150.0,
                        "Operating Income": 120.0,
                        "Net Income": 90.0,
                    },
                    columns[1]: {
                        "Total Revenue": 450.0,
                        "Gross Profit": 130.0,
                        "Operating Income": 100.0,
                        "Net Income": 80.0,
                    },
                }
            ),
            balance_sheet=pd.DataFrame(
                {
                    columns[0]: {
                        "Total Assets": 1000.0,
                        "Total Liabilities Net Minority Interest": 600.0,
                        "Stockholders Equity": 400.0,
                        "Total Debt": 50.0,
                        "Cash And Cash Equivalents": 80.0,
                    }
                }
            ),
            cashflow=pd.DataFrame(
                {
                    columns[0]: {
                        "Operating Cash Flow": 110.0,
                        "Free Cash Flow": 70.0,
                    }
                }
            ),
        )


def universe():
    return [
        UniverseMember("ASELS", "ASELS.IS", "Technology / Defense"),
        UniverseMember("MISS", "MISSING.IS", "Technology / Defense"),
    ]


class YFinanceFundamentalsTest(unittest.TestCase):
    def test_synthetic_disclosure_timestamp_adds_conservative_lag(self):
        self.assertEqual(
            "2024-05-10T18:30:00+03:00",
            synthetic_disclosure_timestamp("2024-03-31", lag_days=40),
        )

    def test_build_yfinance_rows_maps_quarterly_statement_metrics(self):
        member = universe()[0]
        bundle = FakeFundamentalsProvider().fetch(member.yahoo_symbol)

        rows = build_yfinance_fundamentals_rows(
            member=member,
            bundle=bundle,
            download_timestamp="2026-09-24T10:00:00+00:00",
            synthetic_lag_days=40,
        )

        self.assertEqual(2, len(rows))
        latest = rows[1]
        self.assertEqual("ASELS", latest["ticker"])
        self.assertEqual("2024-03-31", latest["period_end"])
        self.assertEqual("2024-05-10T18:30:00+03:00", latest["disclosure_timestamp"])
        self.assertEqual(500.0, latest["revenue"])
        self.assertEqual(70.0, latest["free_cash_flow"])

    def test_fetch_yfinance_fundamentals_writes_normalized_csv_and_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "fundamentals.csv"
            report_path = Path(tmpdir) / "fundamentals_fetch_status.md"

            result = fetch_yfinance_fundamentals(
                universe=universe(),
                output_path=output_path,
                report_path=report_path,
                provider=FakeFundamentalsProvider(),
                download_timestamp="2026-09-24T10:00:00+00:00",
            )

            self.assertEqual(2, len(result.records))
            self.assertEqual(1, len(result.errors))
            self.assertTrue(output_path.exists())
            self.assertTrue(report_path.exists())
            self.assertEqual({"ASELS"}, set(pd.read_csv(output_path)["ticker"]))
            self.assertIn(
                "period_end + 40 days",
                report_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
