import tempfile
import unittest
from pathlib import Path

from src.reporting import (
    REPORT_MANIFEST,
    validate_report_manifest,
    write_final_technical_report,
    write_report_index,
)


class ReportingTests(unittest.TestCase):
    def test_report_manifest_has_required_metadata_and_existing_paths(self):
        errors = validate_report_manifest()

        self.assertEqual([], errors)
        self.assertGreaterEqual(len(REPORT_MANIFEST), 10)
        self.assertIn("Sector catch-up", {entry.report_name for entry in REPORT_MANIFEST})

    def test_write_report_index_contains_required_metadata_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_report_index(Path(tmpdir) / "report_index.md")

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Report Index", text)
            self.assertIn("Data period", text)
            self.assertIn("Sample size", text)
            self.assertIn("Limitations", text)

    def test_write_final_technical_report_marks_strategy_level_findings_inconclusive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_final_technical_report(Path(tmpdir) / "final.md")

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Final Technical Report", text)
            self.assertIn(
                "The four scenario reports, P35 backtest and P36 unseen/regime report contain local-cache measurements",
                text,
            )
            self.assertIn("strategy-level conclusions remain inconclusive", text)
            self.assertIn("No broker connection or investment advice", text)


if __name__ == "__main__":
    unittest.main()
