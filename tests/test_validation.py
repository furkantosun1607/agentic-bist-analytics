import unittest

import pandas as pd

from src.data import MissingSymbol
from src.validation import (
    ANALYSIS_SAFE,
    ANALYSIS_UNSAFE,
    PointInTimeRecord,
    validate_market_dataset,
    validate_no_future_outcome_columns,
    validate_point_in_time_records,
    validate_price_history,
)


def valid_prices(symbol="ASELS.IS"):
    return pd.DataFrame(
        {
            "symbol": [symbol, symbol],
            "date": ["2024-01-02", "2024-01-03"],
            "open": [10.0, 10.5],
            "high": [10.8, 10.9],
            "low": [9.8, 10.1],
            "close": [10.4, 10.7],
            "adj_close": [10.2, 10.6],
            "volume": [1000, 1200],
            "source": ["test", "test"],
            "download_timestamp": [
                "2024-01-04T00:00:00+00:00",
                "2024-01-04T00:00:00+00:00",
            ],
        }
    )


class ValidationTest(unittest.TestCase):
    def test_valid_price_history_is_safe(self):
        report = validate_price_history(
            valid_prices(),
            symbol="ASELS.IS",
            warn_on_small_sample_below=1,
        )

        self.assertEqual(ANALYSIS_SAFE, report.gate_status)
        self.assertEqual((), report.issues)

    def test_small_sample_warns_without_blocking(self):
        report = validate_price_history(
            valid_prices(),
            symbol="ASELS.IS",
            warn_on_small_sample_below=5,
        )

        self.assertEqual(ANALYSIS_SAFE, report.gate_status)
        self.assertEqual(["SMALL_SAMPLE"], [issue.code for issue in report.issues])

    def test_non_monotonic_dates_block_analysis(self):
        prices = valid_prices().iloc[[1, 0]].reset_index(drop=True)

        report = validate_price_history(
            prices,
            symbol="ASELS.IS",
            warn_on_small_sample_below=1,
        )

        self.assertEqual(ANALYSIS_UNSAFE, report.gate_status)
        self.assertIn("NON_MONOTONIC_PRICE_DATES", [issue.code for issue in report.issues])

    def test_price_date_after_download_blocks_analysis(self):
        prices = valid_prices()
        prices.loc[1, "download_timestamp"] = "2024-01-02T00:00:00+00:00"

        report = validate_price_history(
            prices,
            symbol="ASELS.IS",
            warn_on_small_sample_below=1,
        )

        self.assertEqual(ANALYSIS_UNSAFE, report.gate_status)
        self.assertIn("PRICE_DATE_AFTER_DOWNLOAD", [issue.code for issue in report.issues])

    def test_market_dataset_reports_missing_symbols_as_warnings(self):
        report = validate_market_dataset(
            prices_by_symbol={"ASELS.IS": valid_prices()},
            expected_symbols=["ASELS.IS", "XU100.IS"],
            missing_symbols=[MissingSymbol(symbol="XU100.IS", reason="no rows")],
            warn_on_small_sample_below=1,
        )

        self.assertEqual(ANALYSIS_SAFE, report.gate_status)
        self.assertIn("MISSING_SYMBOL", [issue.code for issue in report.issues])
        self.assertIn("EXPECTED_SYMBOL_NOT_FETCHED", [issue.code for issue in report.issues])

    def test_future_publication_blocks_point_in_time_record(self):
        record = PointInTimeRecord(
            record_id="financials-2024q1",
            observation_period_end="2024-03-31",
            publication_timestamp="2024-05-10T18:00:00+03:00",
            download_timestamp="2024-05-11T00:00:00+03:00",
            source="test",
        )

        report = validate_point_in_time_records(
            [record],
            decision_timestamp="2024-05-09T09:30:00+03:00",
        )

        self.assertEqual(ANALYSIS_UNSAFE, report.gate_status)
        self.assertIn("FUTURE_INFORMATION_LEAKAGE", [issue.code for issue in report.issues])

    def test_missing_publication_timestamp_warns(self):
        record = PointInTimeRecord(
            record_id="macro-1",
            observation_period_end="2024-01-31",
            publication_timestamp=None,
            download_timestamp="2024-02-01T00:00:00+03:00",
            source="test",
        )

        report = validate_point_in_time_records(
            [record],
            decision_timestamp="2024-02-02T09:30:00+03:00",
        )

        self.assertEqual(ANALYSIS_SAFE, report.gate_status)
        self.assertEqual(
            ["MISSING_PUBLICATION_TIMESTAMP"],
            [issue.code for issue in report.issues],
        )

    def test_future_outcome_feature_columns_block_analysis(self):
        report = validate_no_future_outcome_columns(
            ["rsi_14", "next_5d_return", "sector"]
        )

        self.assertEqual(ANALYSIS_UNSAFE, report.gate_status)
        self.assertEqual(["FUTURE_OUTCOME_FEATURE"], [issue.code for issue in report.issues])


if __name__ == "__main__":
    unittest.main()
