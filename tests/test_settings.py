import unittest

from src.settings import PROJECT_ROOT, load_settings


class SettingsTest(unittest.TestCase):
    def test_load_settings_from_default_yaml(self):
        settings = load_settings()

        self.assertEqual("agentic-bist-analytics", settings.project.name)
        self.assertEqual("Europe/Istanbul", settings.project.timezone)

    def test_paths_resolve_under_project_root(self):
        settings = load_settings()

        self.assertEqual(PROJECT_ROOT / "config" / "universe.csv", settings.paths.universe)
        self.assertEqual(PROJECT_ROOT / "data" / "cache", settings.paths.cache_dir)
        self.assertEqual(PROJECT_ROOT / "reports", settings.paths.reports_dir)

    def test_backtest_costs_are_nonzero(self):
        settings = load_settings()

        self.assertGreater(settings.backtest.trading_cost_bps, 0)
        self.assertGreater(settings.backtest.slippage_bps, 0)
        self.assertIn(20, settings.backtest.horizons)

    def test_validation_settings_match_fixed_universe(self):
        settings = load_settings()

        self.assertEqual(30, settings.validation.expected_universe_size)
        self.assertTrue(settings.validation.block_on_future_leakage)
        self.assertTrue(settings.validation.block_on_critical_date_mismatch)

    def test_fundamentals_settings_define_synthetic_disclosure_policy(self):
        settings = load_settings()

        self.assertEqual("yahoo_finance", settings.fundamentals.source)
        self.assertEqual(40, settings.fundamentals.synthetic_disclosure_lag_days)
        self.assertEqual("18:30:00", settings.fundamentals.synthetic_disclosure_time)
        self.assertEqual(
            PROJECT_ROOT / "data" / "fundamentals" / "fundamentals.csv",
            settings.fundamentals.output_path,
        )


if __name__ == "__main__":
    unittest.main()
