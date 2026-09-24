import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest import (
    BACKTEST_TRADE_COLUMNS,
    run_backtest,
    write_backtest_report,
)


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
