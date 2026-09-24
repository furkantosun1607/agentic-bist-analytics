import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.context import MACRO_INDICATORS, load_context_csv
from src.macro_context_status import (
    audit_macro_context,
    summarize_macro_indicator_coverage,
)


def macro_rows(indicators=MACRO_INDICATORS):
    rows = []
    for index, indicator in enumerate(indicators, start=1):
        rows.append(
            {
                "context_id": f"macro-{indicator}-2024-01",
                "context_type": "macro",
                "scope": "macro" if indicator != "fed_policy_rate" else "global",
                "indicator": indicator,
                "value": 30.0 + index,
                "unit": "TRY" if indicator in {"usd_try", "eur_try"} else "%",
                "observed_period_start": "2024-01-01",
                "observed_period_end": "2024-01-31",
                "publication_timestamp": "2024-02-01T10:00:00+03:00",
                "download_timestamp": "2024-02-01T10:30:00+03:00",
                "source": "test_macro_source",
                "source_url": "https://example.com/macro",
                "source_access": "public",
            }
        )
    return pd.DataFrame(rows)


class MacroContextStatusTest(unittest.TestCase):
    def test_missing_macro_csv_writes_blocked_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "macro_context.csv"
            report_path = Path(tmpdir) / "macro_context_status.md"

            result = audit_macro_context(
                input_path=missing_path,
                output_path=report_path,
                template_path=Path(tmpdir) / "context_template.csv",
            )

            self.assertEqual("blocked_missing_macro_context_csv", result.status)
            self.assertEqual(0, result.valid_macro_rows)
            self.assertEqual(tuple(MACRO_INDICATORS), result.missing_indicators)
            self.assertIn("User Action", report_path.read_text(encoding="utf-8"))

    def test_complete_macro_csv_reports_ready(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "macro_context.csv"
            report_path = Path(tmpdir) / "macro_context_status.md"
            macro_rows().to_csv(csv_path, index=False)

            result = audit_macro_context(
                input_path=csv_path,
                output_path=report_path,
                decision_timestamp="2024-02-01T11:00:00+03:00",
                template_path=Path(tmpdir) / "context_template.csv",
            )

            self.assertEqual("ready", result.status)
            self.assertEqual(5, result.valid_macro_rows)
            self.assertEqual((), result.missing_indicators)
            self.assertIn("Point-in-time gate: `ANALYSIS_SAFE`", report_path.read_text(encoding="utf-8"))

    def test_partial_macro_csv_reports_source_gaps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "macro_context.csv"
            report_path = Path(tmpdir) / "macro_context_status.md"
            macro_rows(("usd_try", "eur_try")).to_csv(csv_path, index=False)

            result = audit_macro_context(
                input_path=csv_path,
                output_path=report_path,
                decision_timestamp="2024-02-01T11:00:00+03:00",
                template_path=Path(tmpdir) / "context_template.csv",
            )

            self.assertEqual("ready_with_source_gaps", result.status)
            self.assertEqual(2, result.valid_macro_rows)
            self.assertEqual(
                ("tcmb_policy_rate", "tuik_inflation", "fed_policy_rate"),
                result.missing_indicators,
            )

    def test_future_publication_blocks_point_in_time_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "macro_context.csv"
            report_path = Path(tmpdir) / "macro_context_status.md"
            macro_rows().to_csv(csv_path, index=False)

            result = audit_macro_context(
                input_path=csv_path,
                output_path=report_path,
                decision_timestamp="2024-01-31T11:00:00+03:00",
                template_path=Path(tmpdir) / "context_template.csv",
            )

            self.assertEqual("blocked_point_in_time_unsafe", result.status)

    def test_summarize_macro_indicator_coverage_handles_empty_and_populated_records(self):
        self.assertEqual((), summarize_macro_indicator_coverage(pd.DataFrame()))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "macro_context.csv"
            macro_rows(("usd_try",)).to_csv(csv_path, index=False)
            result = audit_macro_context(
                input_path=csv_path,
                output_path=Path(tmpdir) / "macro_context_status.md",
                decision_timestamp="2024-02-01T11:00:00+03:00",
                template_path=Path(tmpdir) / "context_template.csv",
            )

            coverage = summarize_macro_indicator_coverage(load_context_csv(csv_path).records)

            self.assertEqual(1, len(coverage))
            self.assertEqual(result.indicator_coverage[0], coverage[0])


if __name__ == "__main__":
    unittest.main()
