import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.data import UniverseMember
from src.fundamentals import (
    FUNDAMENTALS_COLUMNS,
    empty_fundamentals_frame,
    fundamentals_to_point_in_time_records,
    load_fundamentals_csv,
    metric_profile_for_sector,
    normalize_fundamentals,
    write_fundamentals_schema,
)
from src.validation import ANALYSIS_SAFE, ANALYSIS_UNSAFE, validate_point_in_time_records


def universe():
    return [
        UniverseMember("AKBNK", "AKBNK.IS", "Banking"),
        UniverseMember("ASELS", "ASELS.IS", "Technology / Defense"),
    ]


def raw_records():
    return pd.DataFrame(
        [
            {
                "ticker": "AKBNK",
                "period_end": "2024-03-31",
                "period_type": "quarterly",
                "disclosure_timestamp": "2024-04-29T18:30:00+03:00",
                "download_timestamp": "2024-04-30T09:00:00+03:00",
                "source": "fintables",
                "currency": "TRY",
                "net_income": 100.0,
                "net_interest_income": 250.0,
                "total_assets": 1000.0,
                "total_liabilities": 700.0,
                "total_equity": 300.0,
            },
            {
                "ticker": "ASELS",
                "period_end": "2024-03-31",
                "period_type": "quarterly",
                "disclosure_timestamp": "2024-05-02T19:15:00+03:00",
                "download_timestamp": "2024-05-03T09:00:00+03:00",
                "source": "fintables",
                "currency": "TRY",
                "revenue": 500.0,
                "gross_profit": 150.0,
                "operating_profit": 120.0,
                "net_income": 90.0,
                "total_debt": 50.0,
                "cash_and_equivalents": 80.0,
                "operating_cash_flow": 110.0,
                "free_cash_flow": 70.0,
            },
        ]
    )


class FundamentalsTest(unittest.TestCase):
    def test_normalize_fundamentals_adds_fixed_universe_metadata(self):
        result = normalize_fundamentals(raw_records(), universe())

        self.assertEqual((), result.errors)
        self.assertEqual(list(FUNDAMENTALS_COLUMNS), list(result.records.columns))
        self.assertEqual({"bank", "industrial"}, set(result.records["metric_profile"]))
        self.assertEqual("AKBNK.IS", result.records.loc[0, "yahoo_symbol"])

    def test_metric_profile_for_sector(self):
        self.assertEqual("bank", metric_profile_for_sector("Banking"))
        self.assertEqual("industrial", metric_profile_for_sector("Technology / Defense"))

    def test_row_level_errors_do_not_drop_valid_rows(self):
        raw = raw_records()
        raw.loc[1, "ticker"] = "UNKNOWN"

        result = normalize_fundamentals(raw, universe())

        self.assertEqual(1, len(result.records))
        self.assertEqual(1, len(result.errors))
        self.assertEqual(3, result.errors[0].row_number)
        self.assertIn("not in the fixed universe", result.errors[0].message)

    def test_missing_disclosure_timestamp_is_rejected(self):
        raw = raw_records()
        raw.loc[0, "disclosure_timestamp"] = ""

        result = normalize_fundamentals(raw, universe())

        self.assertEqual(1, len(result.records))
        self.assertIn("missing required value", result.errors[0].message)

    def test_point_in_time_records_validate_against_decision_time(self):
        result = normalize_fundamentals(raw_records(), universe())
        point_in_time = fundamentals_to_point_in_time_records(result.records)

        safe_report = validate_point_in_time_records(
            point_in_time,
            decision_timestamp="2024-05-04T09:30:00+03:00",
        )
        unsafe_report = validate_point_in_time_records(
            point_in_time,
            decision_timestamp="2024-05-01T09:30:00+03:00",
        )

        self.assertEqual(ANALYSIS_SAFE, safe_report.gate_status)
        self.assertEqual(ANALYSIS_UNSAFE, unsafe_report.gate_status)

    def test_load_fundamentals_csv_and_write_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "fundamentals.csv"
            raw_records().to_csv(csv_path, index=False)

            loaded = load_fundamentals_csv(csv_path, universe())
            schema_path = write_fundamentals_schema(Path(tmpdir) / "schema.csv")

            self.assertEqual(2, len(loaded.records))
            self.assertTrue(schema_path.exists())
            self.assertEqual(
                ",".join(FUNDAMENTALS_COLUMNS),
                schema_path.read_text(encoding="utf-8").splitlines()[0],
            )

    def test_empty_fundamentals_frame_has_schema_columns(self):
        self.assertEqual(list(FUNDAMENTALS_COLUMNS), list(empty_fundamentals_frame().columns))


if __name__ == "__main__":
    unittest.main()
