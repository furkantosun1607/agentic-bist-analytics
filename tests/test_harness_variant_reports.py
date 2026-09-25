import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.run_harness_variants import main
from src.harness_variant_reports import load_harness_questions, run_harness_variants


def write_questions(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "question_id,requires_numbers,requires_tools,requires_state_enforcement,requires_evidence,requires_quality_gate,requires_replay,requires_human_review,description",
                "q1,true,true,false,false,false,false,false,Numbers from a tool",
                "q2,true,true,true,true,true,true,true,Full reviewed replay",
            ]
        ),
        encoding="utf-8",
    )


class HarnessVariantReportsTest(unittest.TestCase):
    def test_load_harness_questions_normalizes_boolean_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            questions_path = Path(tmpdir) / "questions.csv"
            write_questions(questions_path)

            questions = load_harness_questions(questions_path)

            self.assertTrue(bool(questions.iloc[0]["requires_numbers"]))
            self.assertFalse(bool(questions.iloc[0]["requires_human_review"]))

    def test_run_harness_variants_writes_measured_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            questions_path = base / "questions.csv"
            reports_dir = base / "reports"
            write_questions(questions_path)

            result = run_harness_variants(
                questions_path=questions_path,
                reports_dir=reports_dir,
            )

            self.assertEqual("measured_deterministic", result.status)
            self.assertEqual(5, len(result.comparison.summary))
            text = (reports_dir / "harness_variants.md").read_text(encoding="utf-8")
            self.assertIn("Deterministic Experiment Run", text)
            self.assertIn("does not call a live LLM", text)

    def test_cli_returns_nonzero_on_orchestrator_failure(self):
        with patch(
            "scripts.run_harness_variants.run_harness_variants_from_settings",
            side_effect=RuntimeError("boom"),
        ):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(1, main([]))
            self.assertIn("status=error", output.getvalue())


if __name__ == "__main__":
    unittest.main()
