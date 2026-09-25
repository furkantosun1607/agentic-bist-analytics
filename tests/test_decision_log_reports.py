import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.run_decision_log import main
from src.decision_log import load_decision_records
from src.decision_log_reports import build_decision_evidence_records, run_decision_log


class DecisionLogReportsTest(unittest.TestCase):
    def test_build_decision_evidence_records_has_source_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            records = build_decision_evidence_records(Path(tmpdir))

            self.assertEqual(4, len(records))
            self.assertEqual({"local_report"}, set(records["source"]))
            self.assertIn("backtest_trade_count", records.columns)

    def test_run_decision_log_writes_single_replayable_record_and_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            reports_dir = base / "reports"
            log_dir = base / "decision_logs"
            reports_dir.mkdir()

            result = run_decision_log(log_dir=log_dir, reports_dir=reports_dir)

            self.assertEqual("reviewed_replay_ok", result.status)
            self.assertEqual("ok", result.replay.status)
            records = load_decision_records(result.log_path)
            self.assertEqual(1, len(records))
            text = result.report_path.read_text(encoding="utf-8")
            self.assertIn("Replay Checks", text)
            self.assertIn("P39 Reviewed Run", text)

    def test_cli_returns_nonzero_on_orchestrator_failure(self):
        with patch(
            "scripts.run_decision_log.run_decision_log_from_settings",
            side_effect=RuntimeError("boom"),
        ):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(1, main([]))
            self.assertIn("status=error", output.getvalue())


if __name__ == "__main__":
    unittest.main()
