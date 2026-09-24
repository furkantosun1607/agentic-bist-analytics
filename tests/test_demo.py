import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from scripts.demo import main
from src.demo import WARNING, run_offline_demo


class DemoTests(unittest.TestCase):
    def test_offline_demo_writes_summary_without_live_cache_requirement(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "demo_summary.md"

            result = run_offline_demo(output_path=output)

            self.assertEqual(0, result.exit_code)
            self.assertTrue(output.exists())
            text = output.read_text(encoding="utf-8")
            self.assertIn("python -m scripts.demo --offline", text)
            self.assertIn("This demo performs no network calls", text)

    def test_offline_demo_marks_missing_cache_as_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "demo_summary.md"

            result = run_offline_demo(output_path=output)

            cache_check = next(check for check in result.checks if check.name == "cache")
            self.assertEqual(WARNING, cache_check.status)

    def test_demo_cli_returns_success_in_offline_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "demo_summary.md"

            with redirect_stdout(StringIO()):
                exit_code = main(["--offline", "--output", str(output)])

            self.assertEqual(0, exit_code)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
