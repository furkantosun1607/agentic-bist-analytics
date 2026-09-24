import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.context import (
    CONTEXT_COLUMNS,
    context_to_point_in_time_records,
    filter_context_for_decision,
    load_context_csv,
    normalize_context,
    write_context_schema,
)
from src.validation import ANALYSIS_SAFE, ANALYSIS_UNSAFE, validate_point_in_time_records


def raw_context_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "context_id": "macro-usdtry-1",
                "context_type": "macro",
                "scope": "macro",
                "indicator": "usd_try",
                "value": 32.5,
                "unit": "TRY",
                "observed_period_start": "2024-01-01",
                "observed_period_end": "2024-01-01",
                "publication_timestamp": "2024-01-01T15:30:00+03:00",
                "download_timestamp": "2024-01-01T16:00:00+03:00",
                "source": "tcmb_evds",
                "source_access": "public",
            },
            {
                "context_id": "news-asels-1",
                "context_type": "news",
                "scope": "company",
                "ticker": "ASELS",
                "title": "ASELS contract",
                "claim": "ASELS announced a contract.",
                "source_url": "https://example.com/news",
                "observed_period_start": "2024-01-02",
                "observed_period_end": "2024-01-02",
                "publication_timestamp": "2024-01-02T10:00:00+03:00",
                "download_timestamp": "2024-01-02T10:05:00+03:00",
                "source": "example_news",
                "source_access": "public",
            },
            {
                "context_id": "video-macro-1",
                "context_type": "video",
                "scope": "macro",
                "title": "Instructor approved macro commentary",
                "claim": "Speaker discussed policy-rate context.",
                "source_url": "https://example.com/video",
                "video_timestamp": "00:03:12",
                "observed_period_start": "2024-01-03",
                "observed_period_end": "2024-01-03",
                "publication_timestamp": "2024-01-03T12:00:00+03:00",
                "download_timestamp": "2024-01-03T12:10:00+03:00",
                "source": "public_video",
                "source_access": "instructor_approved",
            },
        ]
    )


class ContextTests(unittest.TestCase):
    def test_normalize_context_accepts_macro_news_and_video_rows(self):
        result = normalize_context(raw_context_rows())

        self.assertEqual(3, len(result.records))
        self.assertEqual((), result.errors)
        self.assertEqual(list(CONTEXT_COLUMNS), list(result.records.columns))
        self.assertEqual({"macro", "news", "video"}, set(result.records["context_type"]))

    def test_invalid_source_access_is_reported_without_dropping_valid_rows(self):
        raw = raw_context_rows()
        raw.loc[1, "source_access"] = "private"

        result = normalize_context(raw)

        self.assertEqual(2, len(result.records))
        self.assertEqual(1, len(result.errors))
        self.assertIn("source_access must be one of", result.errors[0].message)
        self.assertEqual(3, result.errors[0].row_number)

    def test_invalid_macro_indicator_or_missing_value_is_rejected(self):
        raw = raw_context_rows().iloc[[0]].copy()
        raw.loc[0, "indicator"] = "invented_indicator"

        invalid_indicator = normalize_context(raw)
        self.assertTrue(invalid_indicator.records.empty)
        self.assertIn("macro indicator must be one of", invalid_indicator.errors[0].message)

        raw = raw_context_rows().iloc[[0]].copy()
        raw["value"] = raw["value"].astype(object)
        raw.loc[0, "value"] = ""

        missing_value = normalize_context(raw)
        self.assertTrue(missing_value.records.empty)
        self.assertIn("macro records require numeric value", missing_value.errors[0].message)

    def test_video_requires_timestamp(self):
        raw = raw_context_rows().iloc[[2]].copy()
        raw.loc[2, "video_timestamp"] = ""

        result = normalize_context(raw)

        self.assertTrue(result.records.empty)
        self.assertIn("video records require video_timestamp", result.errors[0].message)

    def test_context_records_pass_point_in_time_gate_only_after_publication(self):
        result = normalize_context(raw_context_rows())
        records = context_to_point_in_time_records(result.records)

        safe_report = validate_point_in_time_records(records, "2024-01-03T13:00:00+03:00")
        unsafe_report = validate_point_in_time_records(records, "2024-01-02T11:00:00+03:00")

        self.assertEqual(ANALYSIS_SAFE, safe_report.gate_status)
        self.assertEqual(ANALYSIS_UNSAFE, unsafe_report.gate_status)
        self.assertIn(
            "FUTURE_INFORMATION_LEAKAGE",
            {issue.code for issue in unsafe_report.issues},
        )

    def test_filter_context_for_decision_keeps_only_public_rows(self):
        result = normalize_context(raw_context_rows())

        filtered = filter_context_for_decision(result.records, "2024-01-02T11:00:00+03:00")

        self.assertEqual(["macro-usdtry-1", "news-asels-1"], list(filtered["context_id"]))

    def test_csv_loader_and_schema_writer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_path = tmp_path / "context.csv"
            schema_path = tmp_path / "schema.csv"
            raw_context_rows().to_csv(input_path, index=False)

            loaded = load_context_csv(input_path)
            written_path = write_context_schema(schema_path)

            self.assertEqual(3, len(loaded.records))
            self.assertEqual((), loaded.errors)
            self.assertEqual(schema_path, written_path)
            self.assertEqual(list(CONTEXT_COLUMNS), list(pd.read_csv(schema_path).columns))


if __name__ == "__main__":
    unittest.main()
