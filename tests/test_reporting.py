import tempfile
import unittest
from pathlib import Path

from src.reporting import (
    REPORT_MANIFEST,
    REQUIREMENT_COVERAGE,
    validate_report_manifest,
    write_final_technical_report,
    write_requirement_coverage,
    write_report_index,
)


class ReportingTests(unittest.TestCase):
    def test_report_manifest_has_required_metadata_and_existing_paths(self):
        errors = validate_report_manifest()

        self.assertEqual([], errors)
        self.assertGreaterEqual(len(REPORT_MANIFEST), 10)
        self.assertIn("Sector catch-up", {entry.report_name for entry in REPORT_MANIFEST})
        self.assertIn(
            "PDF requirement coverage",
            {entry.report_name for entry in REPORT_MANIFEST},
        )
        self.assertIn(
            "Classroom demo notebook",
            {entry.report_name for entry in REPORT_MANIFEST},
        )

    def test_write_report_index_contains_required_metadata_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_report_index(Path(tmpdir) / "report_index.md")

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Report Index", text)
            self.assertIn("Data period", text)
            self.assertIn("Sample size", text)
            self.assertIn("Limitations", text)

    def test_write_requirement_coverage_contains_pdf_alignment_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_requirement_coverage(Path(tmpdir) / "coverage.md")

            text = output.read_text(encoding="utf-8")
            self.assertIn("# PDF Requirement Coverage Matrix", text)
            self.assertIn("Strategy variants A-E", text)
            self.assertIn("video/STT", text)
            self.assertGreaterEqual(len(REQUIREMENT_COVERAGE), 15)

    def test_write_final_technical_report_marks_strategy_level_findings_inconclusive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_final_technical_report(Path(tmpdir) / "final.md")

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Final Technical Report", text)
            self.assertIn(
                "The four scenario reports, P35 backtest, P36 unseen/regime report and P37 A-C strategy variants contain local-cache measurements",
                text,
            )
            self.assertIn(
                "optional LLM explanation run, PDF requirement coverage matrix, classroom demo notebook, static dashboard and reviewed decision replay have measured or generated outputs",
                text,
            )
            self.assertIn("optional LLM harness can run live only when an API key is configured", text)
            self.assertIn("## PDF Requirement Coverage", text)
            self.assertIn("notebooks/01_classroom_demo.ipynb", text)
            self.assertIn("final strategy-level conclusions remain partial", text)
            self.assertIn("No broker connection or investment advice", text)


if __name__ == "__main__":
    unittest.main()
