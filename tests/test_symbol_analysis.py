import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.context import CONTEXT_COLUMNS
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
from src.symbol_analysis import analyze_symbol_from_settings, command_symbol_from_args


class SymbolAnalysisTests(unittest.TestCase):
    def test_command_symbol_accepts_classroom_style_query(self):
        self.assertEqual("ASELS.IS", command_symbol_from_args(["Analyze", "ASELS.IS"]))
        self.assertEqual("ASELS", command_symbol_from_args(["ASELS"]))

    def test_analyze_symbol_writes_readable_demo_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            settings = self._settings(base)
            self._write_universe(settings.paths.universe)
            self._write_price_cache(settings.paths.cache_dir, "ASELS.IS", 10.0)
            self._write_price_cache(settings.paths.cache_dir, "PEER.IS", 12.0)
            fundamentals_path = base / "fundamentals.csv"
            macro_path = base / "macro.csv"
            backtest_path = base / "backtest.md"
            output_path = base / "symbol.md"
            self._write_fundamentals(fundamentals_path)
            self._write_macro(macro_path)
            self._write_backtest(backtest_path)

            result = analyze_symbol_from_settings(
                "ASELS",
                settings=settings,
                output_path=output_path,
                fundamentals_path=fundamentals_path,
                macro_context_path=macro_path,
                backtest_report_path=backtest_path,
            )

            self.assertTrue(output_path.exists())
            self.assertEqual("ASELS.IS", result.symbol)
            self.assertIn("MARKET DATA", result.text)
            self.assertIn("SECTOR ANALYSIS", result.text)
            self.assertIn("TECHNICAL", result.text)
            self.assertIn("HISTORICAL TEST", result.text)
            self.assertIn("FUNDAMENTALS", result.text)
            self.assertIn("MACRO", result.text)
            self.assertIn("BACKTEST", result.text)
            self.assertIn("AI ANALYSIS", result.text)
            self.assertIn("not investment advice", result.text)

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
            experiment=ExperimentConfig(unseen_start_date="2025-10-01", regime_lookback_days=20),
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
            "ticker,yahoo_symbol,sector\nASELS,ASELS.IS,Technology\nPEER,PEER.IS,Technology\n",
            encoding="utf-8",
        )

    def _write_price_cache(self, cache_dir: Path, symbol: str, start: float) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        dates = pd.date_range("2024-01-01", periods=90, freq="D")
        for index, date in enumerate(dates):
            close = start + index * 0.1
            rows.append(
                {
                    "symbol": symbol,
                    "date": date.date().isoformat(),
                    "open": close - 0.05,
                    "high": close + 0.2,
                    "low": close - 0.2,
                    "close": close,
                    "adj_close": close,
                    "volume": 1000 + index,
                    "source": "test",
                    "download_timestamp": "2024-04-01T12:00:00+00:00",
                }
            )
        pd.DataFrame(rows).to_csv(cache_dir / f"{symbol.replace('.', '_')}.csv", index=False)

    def _write_fundamentals(self, path: Path) -> None:
        rows = []
        for index, period in enumerate(pd.date_range("2023-03-31", periods=5, freq="QE")):
            rows.append(
                {
                    "ticker": "ASELS",
                    "period_end": period.date().isoformat(),
                    "period_type": "quarterly",
                    "disclosure_timestamp": (period + pd.Timedelta(days=40)).isoformat(),
                    "download_timestamp": "2024-12-31T12:00:00+00:00",
                    "source": "test",
                    "revenue": 100 + index * 10,
                    "operating_profit": 20 + index * 3,
                }
            )
        pd.DataFrame(rows).to_csv(path, index=False)

    def _write_macro(self, path: Path) -> None:
        rows = []
        for indicator, value, unit in (
            ("usd_try", 34.0, "TRY per USD"),
            ("eur_try", 37.0, "TRY per EUR"),
            ("tcmb_policy_rate", 37.0, "%"),
            ("tuik_inflation", 31.5, "% yoy"),
            ("fed_policy_rate", 3.875, "% target midpoint"),
        ):
            row = {column: "" for column in CONTEXT_COLUMNS}
            row.update(
                {
                    "context_id": f"macro-{indicator}",
                    "context_type": "macro",
                    "scope": "macro",
                    "indicator": indicator,
                    "value": value,
                    "unit": unit,
                    "observed_period_start": "2024-03-31",
                    "observed_period_end": "2024-03-31",
                    "publication_timestamp": "2024-04-01T09:00:00+03:00",
                    "download_timestamp": "2024-04-01T12:00:00+00:00",
                    "source": "test",
                    "source_access": "public",
                }
            )
            rows.append(row)
        pd.DataFrame(rows, columns=list(CONTEXT_COLUMNS)).to_csv(path, index=False)

    def _write_backtest(self, path: Path) -> None:
        path.write_text(
            "\n".join(
                [
                    "# Backtest Report",
                    "",
                    "## Summary",
                    "",
                    "| status | signal_count | trade_count | symbol_count | average_gross_return | median_gross_return | average_cost_adjusted_return | median_cost_adjusted_return | cumulative_return | sharpe_ratio | maximum_drawdown | win_rate | cumulative_benchmark_return | benchmark_difference | average_benchmark_relative_return | average_sector_relative_return |",
                    "|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|",
                    "| ok | 10 | 9 | 2 | 0.01 | 0.01 | 0.008 | 0.007 | 0.25 | 1.5 | -0.10 | 0.55 | 0.15 | 0.10 | 0.02 | 0.01 |",
                ]
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
