import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.data import UniverseMember
from src.fundamentals import normalize_fundamentals
from src.research import (
    ResearchInputError,
    run_quarterly_fundamentals,
    write_quarterly_fundamentals_report,
)


def universe():
    return [
        UniverseMember("ASELS", "ASELS.IS", "Technology / Defense"),
        UniverseMember("FROTO", "FROTO.IS", "Technology / Defense"),
        UniverseMember("AKBNK", "AKBNK.IS", "Banking"),
    ]


def raw_fundamentals():
    rows = []
    periods = ["2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31", "2024-03-31"]
    for index, period in enumerate(periods):
        rows.append(
            {
                "ticker": "ASELS",
                "period_end": period,
                "period_type": "quarterly",
                "disclosure_timestamp": f"2024-0{index + 1}-15T18:30:00+03:00",
                "download_timestamp": f"2024-0{index + 1}-16T09:00:00+03:00",
                "source": "fintables",
                "revenue": 100 + index * 10,
                "gross_profit": 40 + index * 5,
                "operating_profit": 30 + index * 4,
                "net_income": 20 + index * 3,
                "total_assets": 500 + index * 20,
                "total_debt": 100 + index * 5,
                "operating_cash_flow": 25 + index * 2,
                "free_cash_flow": 15 + index,
            }
        )
    rows.append(
        {
            "ticker": "AKBNK",
            "period_end": "2024-03-31",
            "period_type": "quarterly",
            "disclosure_timestamp": "2024-05-10T18:30:00+03:00",
            "download_timestamp": "2024-05-11T09:00:00+03:00",
            "source": "fintables",
            "net_interest_income": 300,
            "net_income": 120,
            "total_assets": 1000,
            "total_liabilities": 800,
            "total_equity": 200,
        }
    )
    return pd.DataFrame(rows)


def normalized_fundamentals():
    return normalize_fundamentals(raw_fundamentals(), universe()).records


def prices(symbol, start=100, rows=120, step=1.0):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = [start + index * step for index in range(rows)]
    return pd.DataFrame(
        {
            "symbol": [symbol] * rows,
            "date": dates.date.astype(str),
            "close": close,
        }
    )


class QuarterlyFundamentalsResearchTest(unittest.TestCase):
    def test_quarterly_fundamentals_generates_metric_observations(self):
        result = run_quarterly_fundamentals(
            fundamentals=normalized_fundamentals(),
            prices_by_symbol={
                "ASELS.IS": prices("ASELS.IS"),
                "FROTO.IS": prices("FROTO.IS", start=200, step=0.5),
                "AKBNK.IS": prices("AKBNK.IS", start=50, step=0.25),
            },
            benchmark_prices=prices("XU100.IS", start=1000, step=2),
            horizons=(1, 5, 20),
        )

        self.assertEqual((), result.errors)
        self.assertGreater(len(result.observations), 0)
        self.assertGreater(len(result.summary), 0)
        self.assertIn("revenue", set(result.observations["metric_name"]))
        self.assertIn("net_interest_income", set(result.observations["metric_name"]))

    def test_qoq_and_yoy_changes_are_calculated(self):
        result = run_quarterly_fundamentals(
            fundamentals=normalized_fundamentals(),
            prices_by_symbol={
                "ASELS.IS": prices("ASELS.IS"),
                "FROTO.IS": prices("FROTO.IS", start=200, step=0.5),
            },
            horizons=(1,),
        )

        rows = result.observations[
            (result.observations["ticker"] == "ASELS")
            & (result.observations["period_end"] == "2024-03-31")
            & (result.observations["metric_name"] == "revenue")
        ]

        self.assertGreater(len(rows), 0)
        self.assertAlmostEqual((140 - 130) / 130, rows.iloc[0]["qoq_change"])
        self.assertAlmostEqual((140 - 100) / 100, rows.iloc[0]["yoy_change"])

    def test_post_disclosure_return_uses_next_trading_day_entry(self):
        bank_record = normalized_fundamentals()
        bank_record = bank_record[bank_record["ticker"] == "AKBNK"]

        result = run_quarterly_fundamentals(
            fundamentals=bank_record,
            prices_by_symbol={"AKBNK.IS": prices("AKBNK.IS", start=50, step=1)},
            horizons=(1,),
        )

        row = result.observations[result.observations["status"] == "ok"].iloc[0]
        self.assertGreater(row["entry_date"], "2024-05-10")
        self.assertGreater(row["post_disclosure_return"], 0)

    def test_bank_records_do_not_emit_industrial_margin_metrics(self):
        bank_record = normalized_fundamentals()
        bank_record = bank_record[bank_record["ticker"] == "AKBNK"]

        result = run_quarterly_fundamentals(
            fundamentals=bank_record,
            prices_by_symbol={"AKBNK.IS": prices("AKBNK.IS")},
            horizons=(1,),
        )

        self.assertNotIn("gross_margin", set(result.observations["metric_name"]))
        self.assertIn("net_interest_income", set(result.observations["metric_name"]))

    def test_missing_price_history_is_structured_error(self):
        result = run_quarterly_fundamentals(
            fundamentals=normalized_fundamentals().head(1),
            prices_by_symbol={},
            horizons=(1,),
        )

        self.assertEqual(0, len(result.observations))
        self.assertIn("missing price history", result.errors[0].message)

    def test_missing_disclosure_timestamp_returns_research_error(self):
        records = normalized_fundamentals()
        records.loc[0, "disclosure_timestamp"] = pd.NA

        result = run_quarterly_fundamentals(
            fundamentals=records,
            prices_by_symbol={"ASELS.IS": prices("ASELS.IS")},
            horizons=(1,),
        )

        self.assertEqual(0, len(result.observations))
        self.assertIn("disclosure_timestamp", result.errors[0].message)

    def test_invalid_horizon_raises_clear_error(self):
        with self.assertRaisesRegex(ResearchInputError, "horizons must be positive"):
            run_quarterly_fundamentals(
                fundamentals=normalized_fundamentals(),
                prices_by_symbol={"ASELS.IS": prices("ASELS.IS")},
                horizons=(0,),
            )

    def test_write_quarterly_fundamentals_report(self):
        result = run_quarterly_fundamentals(
            fundamentals=normalized_fundamentals().head(2),
            prices_by_symbol={"ASELS.IS": prices("ASELS.IS")},
            horizons=(1,),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_quarterly_fundamentals_report(
                result,
                Path(tmpdir) / "quarterly_fundamentals.md",
            )

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Quarterly Fundamentals Report", text)
            self.assertIn("disclosure timestamp", text)


if __name__ == "__main__":
    unittest.main()
