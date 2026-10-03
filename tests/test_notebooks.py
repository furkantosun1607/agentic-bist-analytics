import json
import unittest
from pathlib import Path


NOTEBOOK_PATH = Path("notebooks/01_classroom_demo.ipynb")


class NotebookTests(unittest.TestCase):
    def test_classroom_demo_notebook_is_valid_and_secret_free(self):
        raw = NOTEBOOK_PATH.read_text(encoding="utf-8")
        notebook = json.loads(raw)

        self.assertEqual(4, notebook["nbformat"])
        self.assertGreaterEqual(len(notebook["cells"]), 8)
        self.assertIn("Full Local Workflow", raw)
        self.assertIn("reports/pdf_requirement_coverage.md", raw)
        self.assertIn("reports/llm_agent_harness.json", raw)
        self.assertNotIn("AQ.", raw)
        self.assertNotIn("GEMINI_API_KEY=\"", raw)


if __name__ == "__main__":
    unittest.main()
