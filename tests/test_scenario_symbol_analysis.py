import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.settings import (
    BacktestConfig,
    ExperimentConfig,
    FundamentalsConfig,
    MarketDataConfig,
    OutputConfig,
    PathConfig,
    ProjectConfig,
    Settings,
    ValidationConfig,
)
from src.scenario_symbol_analysis import (
    analyze_fundamentals_reaction_from_settings,
    analyze_sector_catchup_from_settings,
    analyze_technical_reversal_from_settings,
    analyze_weekday_pattern_from_settings,
)


class ScenarioSymbolAnalysisTests(unittest.TestCase):
    def test_four_scenario_commands_write_readable_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            settings = self._settings(base)
            self._write_universe(settings.paths.universe)
            self._write_price_cache(settings.paths.cache_dir, "AAA.IS", 100.0)
            self._write_price_cache(settings.paths.cache_dir, "BBB.IS", 110.0)
            self._write_price_cache(settings.paths.cache_dir, "XU100.IS", 1000.0)
            fundamentals_path = base / "fundamentals.csv"
            self._write_fundamentals(fundamentals_path)

            sector = analyze_sector_catchup_from_settings(
                "AAA.IS",
                settings=settings,
                output_path=base / "sector.md",
            )
            weekday = analyze_weekday_pattern_from_settings(
                "AAA.IS",
                settings=settings,
                output_path=base / "weekday.md",
            )
            technical = analyze_technical_reversal_from_settings(
                "AAA.IS",
                settings=settings,
                output_path=base / "technical.md",
            )
            fundamentals = analyze_fundamentals_reaction_from_settings(
                "AAA.IS",
                settings=settings,
                output_path=base / "fundamentals.md",
                fundamentals_path=fundamentals_path,
            )

            self.assertTrue(sector.report_path.exists())
            self.assertIn("Sector Laggard", sector.text)
            self.assertIn("HISTORICAL LAGGARD OUTCOMES", sector.text)
            self.assertTrue(weekday.report_path.exists())
            self.assertIn("Weekday / Multi-Day Pattern", weekday.text)
            self.assertIn("MULTIPLE-TESTING RISK", weekday.text)
            self.assertTrue(technical.report_path.exists())
            self.assertIn("Technical Reversal", technical.text)
            self.assertIn("HISTORICAL EVENT TEST", technical.text)
            self.assertTrue(fundamentals.report_path.exists())
            self.assertIn("Quarterly Fundamentals", fundamentals.text)
            self.assertIn("PRICE REACTION AFTER DISCLOSURE", fundamentals.text)

    def _settings(self, base: Path) -> Settings:
        return Settings(
            project=ProjectConfig(name="test", timezone="Europe/Istanbul"),
            paths=PathConfig(
                universe=base / "universe.csv",
                cache_dir=base / "cache",
                reports_dir=base / "reports",
                notebooks_dir=base / "notebooks",
            ),
            market_data=MarketDataConfig(
                benchmark_symbol="XU100.IS",
                price_source="test",
                adjusted_price_policy="close",
                start_date="2024-01-01",
                end_date=None,
            ),
            fundamentals=FundamentalsConfig(
                source="test",
                output_path=base / "fundamentals.csv",
                synthetic_disclosure_lag_days=40,
                synthetic_disclosure_time="18:30:00",
            ),
            backtest=BacktestConfig(
                entry_timing="next_trading_day_open",
                exit_timing="close_after_horizon",
                trading_cost_bps=10.0,
                slippage_bps=5.0,
                horizons=(1, 3, 5, 10, 20),
            ),
            experiment=ExperimentConfig(unseen_start_date="2024-05-01", regime_lookback_days=5),
            validation=ValidationConfig(
                expected_universe_size=2,
                block_on_future_leakage=True,
                block_on_critical_date_mismatch=True,
                warn_on_small_sample_below=20,
            ),
            outputs=OutputConfig(report_format="markdown", decision_log_dir=base / "decision_logs"),
        )

    def _write_universe(self, path: Path) -> None:
        path.write_text(
            "ticker,yahoo_symbol,sector\nAAA,AAA.IS,Test Sector\nBBB,BBB.IS,Test Sector\n",
            encoding="utf-8",
        )

    def _write_price_cache(self, cache_dir: Path, symbol: str, start: float) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        dates = pd.date_range("2024-01-01", periods=180, freq="B")
        rows = []
        for index, date in enumerate(dates):
            close = start + (index * 0.2) + ((-1) ** index) * 1.5
            rows.append(
                {
                    "symbol": symbol,
                    "date": date.date().isoformat(),
                    "open": close - 0.2,
                    "high": close + 0.5,
                    "low": close - 0.5,
                    "close": close,
                    "adj_close": close,
                    "volume": 1000 + (index % 10) * 100,
                    "source": "test",
                    "download_timestamp": "2024-12-31T12:00:00+00:00",
                }
            )
        pd.DataFrame(rows).to_csv(cache_dir / f"{symbol.replace('.', '_')}.csv", index=False)

    def _write_fundamentals(self, path: Path) -> None:
        rows = []
        periods = pd.date_range("2023-03-31", periods=5, freq="QE")
        for index, period in enumerate(periods):
            rows.append(
                {
                    "ticker": "AAA",
                    "period_end": period.date().isoformat(),
                    "period_type": "quarterly",
                    "disclosure_timestamp": (period + pd.Timedelta(days=40)).isoformat(),
                    "download_timestamp": "2024-12-31T12:00:00+00:00",
                    "source": "test",
                    "revenue": 100 + index * 8,
                    "operating_profit": 20 + index * 2,
                    "operating_cash_flow": 15 + index,
                    "free_cash_flow": 10 + index,
                    "total_assets": 500 + index * 20,
                    "total_debt": 80 + index * 2,
                }
            )
        pd.DataFrame(rows).to_csv(path, index=False)


if __name__ == "__main__":
    unittest.main()
