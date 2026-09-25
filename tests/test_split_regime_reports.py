import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.run_split_regime import main
from src.backtest_reports import BacktestReportRunResult
from src.backtest import BacktestResult
from src.data import UniverseMember, write_price_cache
from src.split_regime_reports import (
    label_backtest_trades_for_split_regime,
    run_split_regime,
    summarize_regime_counts,
)


def trades():
    return pd.DataFrame(
        [
            {
                "signal_id": "a",
                "symbol": "AAA.IS",
                "source": "technical",
                "known_at": "2024-01-02T18:10:00+03:00",
                "direction": "long",
                "horizon": 5,
                "status": "ok",
                "entry_timing": "next_trading_day_open",
                "exit_timing": "close_after_horizon",
                "entry_date": "2024-01-03",
                "entry_price": 100.0,
                "exit_date": "2024-01-10",
                "exit_price": 104.0,
                "gross_return": 0.04,
                "trading_cost_bps": 10.0,
                "slippage_bps": 5.0,
                "total_cost_bps": 15.0,
                "cost_adjusted_return": 0.0385,
                "benchmark_return": 0.01,
                "benchmark_relative_return": 0.03,
                "sector": "Technology",
                "sector_benchmark_return": pd.NA,
                "sector_relative_return": pd.NA,
                "buy_hold_return": 0.04,
            },
            {
                "signal_id": "b",
                "symbol": "AAA.IS",
                "source": "technical",
                "known_at": "2025-10-02T18:10:00+03:00",
                "direction": "long",
                "horizon": 5,
                "status": "ok",
                "entry_timing": "next_trading_day_open",
                "exit_timing": "close_after_horizon",
                "entry_date": "2025-10-03",
                "entry_price": 105.0,
                "exit_date": "2025-10-10",
                "exit_price": 103.0,
                "gross_return": -0.019,
                "trading_cost_bps": 10.0,
                "slippage_bps": 5.0,
                "total_cost_bps": 15.0,
                "cost_adjusted_return": -0.0205,
                "benchmark_return": -0.01,
                "benchmark_relative_return": -0.009,
                "sector": "Technology",
                "sector_benchmark_return": pd.NA,
                "sector_relative_return": pd.NA,
                "buy_hold_return": 0.03,
            },
        ]
    )


def benchmark():
    return pd.DataFrame(
        {
            "date": ["2024-01-02", "2025-10-02"],
            "close": [1000.0, 1100.0],
        }
    )


def price_frame(symbol, start=100.0, rows=560, step=0.1):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = pd.Series([start + index * step for index in range(rows)])
    return pd.DataFrame(
        {
            "symbol": [symbol] * rows,
            "date": dates.date.astype(str),
            "open": close - 0.1,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "adj_close": close,
            "volume": [1000 + index for index in range(rows)],
            "source": ["test"] * rows,
            "download_timestamp": ["2026-09-25T00:00:00+00:00"] * rows,
        }
    )


def fundamentals_records():
    return pd.DataFrame(
        [
            {
                "ticker": "ASELS",
                "period_end": "2024-03-31",
                "period_type": "quarterly",
                "disclosure_timestamp": "2024-04-15T18:30:00+03:00",
                "download_timestamp": "2024-04-16T09:00:00+03:00",
                "source": "test",
                "currency": "TRY",
                "revenue": 100.0,
                "gross_profit": 40.0,
                "operating_profit": 30.0,
                "net_income": 20.0,
                "total_assets": 500.0,
                "total_debt": 100.0,
                "operating_cash_flow": 25.0,
                "free_cash_flow": 15.0,
            }
        ]
    )


class SplitRegimeReportsTest(unittest.TestCase):
    def test_label_backtest_trades_for_split_regime_uses_known_at_date(self):
        labeled, warnings = label_backtest_trades_for_split_regime(
            trades=trades(),
            unseen_start_date="2025-10-01",
            benchmark_prices=benchmark(),
            regime_lookback_days=1,
        )

        self.assertEqual((), warnings)
        self.assertEqual(["selection", "unseen"], list(labeled["period_split"]))
        self.assertIn("market_regime", labeled.columns)
        self.assertEqual("2024-01-02", labeled.iloc[0]["signal_date"])

    def test_summarize_regime_counts_reports_trade_count(self):
        labeled, _ = label_backtest_trades_for_split_regime(
            trades=trades(),
            unseen_start_date="2025-10-01",
            benchmark_prices=benchmark(),
            regime_lookback_days=1,
        )

        summary = summarize_regime_counts(labeled)

        self.assertEqual(2, int(summary["trade_count"].sum()))
        self.assertIn("average_return", summary.columns)

    def test_run_split_regime_writes_measured_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            cache_dir = base / "cache"
            reports_dir = base / "reports"
            fundamentals_path = base / "fundamentals.csv"

            write_price_cache(price_frame("ASELS.IS", start=100, step=0.02), cache_dir, "ASELS.IS")
            write_price_cache(price_frame("FROTO.IS", start=200, step=0.04), cache_dir, "FROTO.IS")
            write_price_cache(price_frame("XU100.IS", start=1000, step=0.5), cache_dir, "XU100.IS")
            fundamentals_records().to_csv(fundamentals_path, index=False)

            result = run_split_regime(
                universe=[
                    UniverseMember("ASELS", "ASELS.IS", "Technology / Defense"),
                    UniverseMember("FROTO", "FROTO.IS", "Technology / Defense"),
                ],
                cache_dir=cache_dir,
                reports_dir=reports_dir,
                benchmark_symbol="XU100.IS",
                fundamentals_path=fundamentals_path,
                unseen_start_date="2025-01-01",
                horizons=(1, 3, 5, 10, 20),
                regime_lookback_days=5,
            )

            self.assertEqual("measured", result.status)
            self.assertGreater(len(result.stability_summary), 0)
            text = (reports_dir / "split_regime.md").read_text(encoding="utf-8")
            self.assertIn("Unseen start date", text)
            self.assertIn("Stability Summary", text)

    def test_cli_returns_nonzero_on_orchestrator_failure(self):
        with patch(
            "scripts.run_split_regime.run_split_regime_from_settings",
            side_effect=RuntimeError("boom"),
        ):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(1, main([]))
            self.assertIn("status=error", output.getvalue())


if __name__ == "__main__":
    unittest.main()
