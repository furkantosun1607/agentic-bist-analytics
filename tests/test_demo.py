import tempfile
import unittest
from unittest.mock import patch
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
            temp_path = Path(tmpdir)
            output = temp_path / "demo_summary.md"
            settings = _write_temp_settings(temp_path)

            result = run_offline_demo(settings_path=settings, output_path=output)

            cache_check = next(check for check in result.checks if check.name == "cache")
            self.assertEqual(WARNING, cache_check.status)

    def test_offline_demo_marks_missing_rss_artifacts_as_warnings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            output = temp_path / "demo_summary.md"

            with (
                patch("src.demo.DEFAULT_RSS_OUTPUT_PATH", temp_path / "missing_raw.jsonl"),
                patch("src.demo.DEFAULT_NORMALIZED_RSS_OUTPUT_PATH", temp_path / "missing_news.jsonl"),
                patch("src.demo.DEFAULT_MATCHED_NEWS_OUTPUT_PATH", temp_path / "missing_matched.jsonl"),
                patch("src.demo.DEFAULT_NEWS_CONTEXT_OUTPUT_PATH", temp_path / "missing_context.csv"),
                patch("src.demo.DEFAULT_RSS_SOURCE_HEALTH_PATH", temp_path / "missing_health.md"),
            ):
                result = run_offline_demo(output_path=output)

            by_name = {check.name: check for check in result.checks}
            self.assertEqual(WARNING, by_name["rss_raw_cache"].status)
            self.assertEqual(WARNING, by_name["rss_normalized_cache"].status)
            self.assertEqual(WARNING, by_name["rss_matched_cache"].status)
            self.assertEqual(WARNING, by_name["rss_context"].status)
            self.assertEqual(WARNING, by_name["rss_source_health"].status)

    def test_offline_demo_reports_existing_rss_context_artifacts(self):
        result = run_offline_demo()

        by_name = {check.name: check for check in result.checks}
        self.assertIn(by_name["rss_raw_cache"].status, {"pass", "warning"})
        self.assertIn(by_name["rss_context"].status, {"pass", "warning"})
        summary = result.summary_path.read_text(encoding="utf-8")
        self.assertIn("## RSS News Context", summary)

    def test_demo_cli_returns_success_in_offline_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "demo_summary.md"

            with redirect_stdout(StringIO()):
                exit_code = main(["--offline", "--output", str(output)])

            self.assertEqual(0, exit_code)
            self.assertTrue(output.exists())

def _write_temp_settings(base_path: Path) -> Path:
    settings_path = base_path / "settings.yaml"
    cache_dir = (base_path / "empty_cache").as_posix()
    reports_dir = (base_path / "reports").as_posix()
    decision_log_dir = (base_path / "decision_logs").as_posix()
    settings_path.write_text(
        "\n".join(
            [
                "project:",
                "  name: agentic-bist-analytics-test",
                "  timezone: Europe/Istanbul",
                "",
                "paths:",
                "  universe: config/universe.csv",
                f"  cache_dir: {cache_dir}",
                f"  reports_dir: {reports_dir}",
                "  notebooks_dir: notebooks",
                "",
                "market_data:",
                "  benchmark_symbol: XU100.IS",
                "  price_source: yahoo_finance",
                "  adjusted_price_policy: use_adjusted_close_when_available",
                "  start_date: 2021-01-01",
                "  end_date: null",
                "",
                "fundamentals:",
                "  source: yahoo_finance",
                f"  output_path: {(base_path / 'fundamentals.csv').as_posix()}",
                "  synthetic_disclosure_lag_days: 40",
                '  synthetic_disclosure_time: "18:30:00"',
                "",
                "backtest:",
                "  entry_timing: next_trading_day_open",
                "  exit_timing: close_after_horizon",
                "  trading_cost_bps: 10",
                "  slippage_bps: 5",
                "  horizons: [1, 3, 5, 10, 20]",
                "",
                "experiment:",
                "  unseen_start_date: null",
                "  regime_lookback_days: 20",
                "",
                "validation:",
                "  expected_universe_size: 30",
                "  block_on_future_leakage: true",
                "  block_on_critical_date_mismatch: true",
                "  warn_on_small_sample_below: 20",
                "",
                "outputs:",
                "  report_format: markdown",
                f"  decision_log_dir: {decision_log_dir}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return settings_path


if __name__ == "__main__":
    unittest.main()
