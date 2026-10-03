import tempfile
import unittest
from pathlib import Path

from src.ui_dashboard import build_dashboard


class UIDashboardTests(unittest.TestCase):
    def test_build_dashboard_writes_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "dashboard.html"

            result = build_dashboard(output_path=output)

            self.assertTrue(output.exists())
            self.assertGreater(result.report_count, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("Agentic BIST Analytics Dashboard", text)
            self.assertIn("LLM Agent Explanation", text)
            self.assertIn("Submission Shortcuts", text)
            self.assertIn("reports/pdf_requirement_coverage.md", text)
            self.assertIn("notebooks/01_classroom_demo.ipynb", text)
            self.assertIn("python -m scripts.run_llm_agent_harness", text)


if __name__ == "__main__":
    unittest.main()
