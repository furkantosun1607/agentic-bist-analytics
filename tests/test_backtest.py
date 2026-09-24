import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest import (
    BACKTEST_TRADE_COLUMNS,
    calculate_risk_metrics,
    run_backtest,
    run_backtest_from_settings,
    write_backtest_report,
)
from src.settings import load_settings


def prices(symbol="AAA.IS", closes=None, opens=None):
    if closes is None:
        closes = [100, 101, 103, 106, 110, 111, 115]
    if opens is None:
        opens = [close - 0.5 for close in closes]
    dates = pd.date_range("2024-01-01", periods=len(closes), freq="B")
    return pd.DataFrame(
        {
            "symbol": [symbol] * len(closes),
            "date": dates.date.astype(str),
            "open": opens,
            "close": closes,
        }
    )


def signals():
    return pd.DataFrame(
        [
            {
                "signal_id": "sig-1",
                "symbol": "AAA.IS",
                "known_at": "2024-01-01T18:10:00+03:00",
                "horizon": 2,
                "direction": "long",
                "source": "unit_test",
            }
        ]
    )


class BacktestTests(unittest.TestCase):
    def test_backtest_uses_first_trading_day_after_signal_known_at(self):
        result = run_backtest(
            signals=signals(),
            prices_by_symbol={"AAA.IS": prices()},
            default_horizon=1,
        )

        row = result.trades.iloc[0]
        self.assertEqual((), result.errors)
        self.assertEqual("ok", row["status"])
        self.assertEqual("2024-01-02", row["entry_date"])
        self.assertEqual(100.5, row["entry_price"])
        self.assertEqual("2024-01-04", row["exit_date"])
        self.assertAlmostEqual(106 / 100.5 - 1, row["gross_return"])
        self.assertEqual(list(BACKTEST_TRADE_COLUMNS), list(result.trades.columns))

    def test_benchmark_and_sector_relative_returns_are_reported_when_available(self):
        result = run_backtest(
            signals=signals(),
            prices_by_symbol={"AAA.IS": prices()},
            benchmark_prices=prices("XU100.IS", closes=[1000, 1005, 1010, 1020, 1030]),
            sector_benchmark_prices={
                "Technology": prices("TECH", closes=[200, 202, 204, 208, 212])
            },
            symbol_to_sector={"AAA.IS": "Technology"},
        )

        row = result.trades.iloc[0]
        expected_benchmark = 1020 / 1005 - 1
        expected_sector = 208 / 202 - 1
        self.assertAlmostEqual(expected_benchmark, row["benchmark_return"])
        self.assertAlmostEqual(row["gross_return"] - expected_benchmark, row["benchmark_relative_return"])
        self.assertAlmostEqual(expected_sector, row["sector_benchmark_return"])
        self.assertAlmostEqual(row["gross_return"] - expected_sector, row["sector_relative_return"])
        self.assertEqual(1, result.summary.iloc[0]["signal_count"])
        self.assertEqual(1, result.summary.iloc[0]["trade_count"])
        self.assertIn("cumulative_return", result.summary.columns)

    def test_cost_adjusted_return_deducts_trading_cost_and_slippage(self):
        result = run_backtest(
            signals=signals(),
            prices_by_symbol={"AAA.IS": prices()},
            trading_cost_bps=20,
            slippage_bps=5,
        )

        row = result.trades.iloc[0]
        self.assertEqual(20.0, row["trading_cost_bps"])
        self.assertEqual(5.0, row["slippage_bps"])
        self.assertEqual(25.0, row["total_cost_bps"])
        self.assertAlmostEqual(row["gross_return"] - 0.0025, row["cost_adjusted_return"])
        self.assertAlmostEqual(
            row["cost_adjusted_return"],
            result.summary.iloc[0]["average_cost_adjusted_return"],
        )

    def test_backtest_can_read_cost_and_timing_assumptions_from_settings(self):
        settings = load_settings()

        result = run_backtest_from_settings(
            signals=signals().drop(columns=["horizon"]),
            prices_by_symbol={"AAA.IS": prices()},
            settings=settings,
        )

        row = result.trades.iloc[0]
        self.assertEqual(settings.backtest.entry_timing, row["entry_timing"])
        self.assertEqual(settings.backtest.exit_timing, row["exit_timing"])
        self.assertEqual(settings.backtest.horizons[0], row["horizon"])
        self.assertEqual(settings.backtest.trading_cost_bps, row["trading_cost_bps"])
        self.assertEqual(settings.backtest.slippage_bps, row["slippage_bps"])

    def test_risk_metrics_include_cumulative_return_drawdown_sharpe_and_win_rate(self):
        trades = pd.DataFrame(
            {
                "signal_id": ["a", "b", "c"],
                "exit_date": ["2024-01-03", "2024-01-04", "2024-01-05"],
                "cost_adjusted_return": [0.10, -0.20, 0.05],
                "benchmark_return": [0.05, -0.10, 0.02],
            }
        )

        metrics = calculate_risk_metrics(trades)

        self.assertAlmostEqual((1.10 * 0.80 * 1.05) - 1, metrics["cumulative_return"])
        self.assertAlmostEqual((1.05 * 0.90 * 1.02) - 1, metrics["cumulative_benchmark_return"])
        self.assertAlmostEqual(2 / 3, metrics["win_rate"])
        self.assertLess(metrics["maximum_drawdown"], 0)
        self.assertIsInstance(metrics["sharpe_ratio"], float)

    def test_zero_total_cost_is_rejected(self):
        result = run_backtest(
            signals=signals(),
            prices_by_symbol={"AAA.IS": prices()},
            trading_cost_bps=0,
            slippage_bps=0,
        )

        self.assertTrue(result.trades.empty)
        self.assertIn("must be nonzero", result.errors[0].message)

    def test_missing_price_history_is_trade_status_not_crash(self):
        result = run_backtest(
            signals=signals(),
            prices_by_symbol={"BBB.IS": prices("BBB.IS")},
        )

        self.assertEqual("missing_price_history", result.trades.iloc[0]["status"])
        self.assertEqual(0, result.summary.iloc[0]["trade_count"])

    def test_unsupported_direction_is_reported_as_status(self):
        raw = signals()
        raw.loc[0, "direction"] = "short"

        result = run_backtest(
            signals=raw,
            prices_by_symbol={"AAA.IS": prices()},
        )

        self.assertEqual("unsupported_direction", result.trades.iloc[0]["status"])

    def test_structural_signal_error_is_returned(self):
        result = run_backtest(
            signals=signals().drop(columns=["known_at"]),
            prices_by_symbol={"AAA.IS": prices()},
        )

        self.assertTrue(result.trades.empty)
        self.assertIn("missing required columns", result.errors[0].message)

    def test_invalid_price_history_is_structured_error_without_dropping_other_symbols(self):
        result = run_backtest(
            signals=pd.concat(
                [
                    signals(),
                    pd.DataFrame(
                        [
                            {
                                "signal_id": "sig-2",
                                "symbol": "BBB.IS",
                                "known_at": "2024-01-01T18:10:00+03:00",
                                "horizon": 1,
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            ),
            prices_by_symbol={
                "AAA.IS": prices(),
                "BBB.IS": pd.DataFrame({"date": ["2024-01-01"], "close": [-1]}),
            },
        )

        self.assertIn("BBB.IS", {error.scope for error in result.errors})
        self.assertEqual(["ok", "missing_price_history"], list(result.trades["status"]))

    def test_write_backtest_report(self):
        result = run_backtest(
            signals=signals(),
            prices_by_symbol={"AAA.IS": prices()},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_backtest_report(result, Path(tmpdir) / "backtest.md")

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Backtest Report", text)
            self.assertIn("Status Counts", text)


if __name__ == "__main__":
    unittest.main()
