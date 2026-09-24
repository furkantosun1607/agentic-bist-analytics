import tempfile
import unittest
from pathlib import Path

from tests.test_fundamentals import raw_records, universe

from src.fundamentals import empty_fundamentals_frame, normalize_fundamentals
from src.fundamentals_status import (
    audit_fundamentals_import,
    summarize_fundamentals_coverage,
)


class FundamentalsStatusTest(unittest.TestCase):
    def test_missing_local_csv_writes_blocked_status_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "fundamentals.csv"
            report_path = Path(tmpdir) / "fundamentals_import_status.md"

            result = audit_fundamentals_import(
                input_path=missing_path,
                output_path=report_path,
                universe_path=Path("config/universe.csv"),
                template_path=Path(tmpdir) / "template.csv",
            )

            self.assertEqual("blocked_missing_fundamentals_csv", result.status)
            self.assertEqual(0, result.valid_rows)
            self.assertTrue(report_path.exists())
            text = report_path.read_text(encoding="utf-8")
            self.assertIn("User Decision Needed", text)
            self.assertIn("data/fundamentals/fundamentals.csv", text)

    def test_valid_local_csv_reports_ready_with_coverage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "fundamentals.csv"
            report_path = Path(tmpdir) / "fundamentals_import_status.md"
            raw_records().to_csv(csv_path, index=False)

            result = audit_fundamentals_import(
                input_path=csv_path,
                output_path=report_path,
                universe_path=Path("config/universe.csv"),
                decision_timestamp="2024-05-04T09:30:00+03:00",
                template_path=Path(tmpdir) / "template.csv",
            )

            self.assertEqual("ready", result.status)
            self.assertEqual(2, result.valid_rows)
            self.assertEqual(2, result.universe_coverage)
            self.assertEqual(2, len(result.coverage_rows))
            self.assertIn("| AKBNK | bank | 1 |", report_path.read_text(encoding="utf-8"))

    def test_import_warnings_are_preserved_when_valid_rows_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "fundamentals.csv"
            report_path = Path(tmpdir) / "fundamentals_import_status.md"
            raw = raw_records()
            raw.loc[1, "ticker"] = "UNKNOWN"
            raw.to_csv(csv_path, index=False)

            result = audit_fundamentals_import(
                input_path=csv_path,
                output_path=report_path,
                universe_path=Path("config/universe.csv"),
                decision_timestamp="2024-05-04T09:30:00+03:00",
                template_path=Path(tmpdir) / "template.csv",
            )

            self.assertEqual("ready_with_import_warnings", result.status)
            self.assertEqual(1, result.valid_rows)
            self.assertEqual(1, result.error_count)
            self.assertIn("not in the fixed universe", report_path.read_text(encoding="utf-8"))

    def test_summarize_coverage_returns_metric_fields_by_ticker(self):
        self.assertEqual((), summarize_fundamentals_coverage(empty_fundamentals_frame()))

        normalized = normalize_fundamentals(raw_records(), universe())
        coverage = summarize_fundamentals_coverage(normalized.records)

        self.assertEqual(("AKBNK", "ASELS"), tuple(row.ticker for row in coverage))
        self.assertEqual("bank", coverage[0].metric_profile)
        self.assertIn("net_income", coverage[0].populated_numeric_fields)


if __name__ == "__main__":
    unittest.main()
