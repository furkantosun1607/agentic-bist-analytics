import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.run_backtests import main
from src.backtest_reports import assemble_backtest_signals, run_backtests
from src.data import UniverseMember, write_price_cache


def price_frame(symbol, start=100.0, rows=90, step=0.5):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = pd.Series([start + index * step for index in range(rows)])
    return pd.DataFrame(
        {
            "symbol": [symbol] * rows,
            "date": dates.date.astype(str),
            "open": close - 0.2,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "adj_close": close,
            "volume": [1000 + index for index in range(rows)],
            "source": ["test"] * rows,
            "download_timestamp": ["2026-09-25T00:00:00+00:00"] * rows,
        }
    )


def universe():
    return [
        UniverseMember("ASELS", "ASELS.IS", "Technology / Defense"),
        UniverseMember("FROTO", "FROTO.IS", "Technology / Defense"),
    ]


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


class BacktestReportsTest(unittest.TestCase):
    def test_assemble_backtest_signals_uses_fixed_rules_not_future_returns(self):
        sector = pd.DataFrame(
            [
                {
                    "symbol": "ASELS.IS",
                    "date": "2024-01-10",
                    "horizon": 5,
                    "status": "ok",
                    "is_laggard": True,
                    "future_return": -0.99,
                },
                {
                    "symbol": "FROTO.IS",
                    "date": "2024-01-10",
                    "horizon": 5,
                    "status": "ok",
                    "is_laggard": False,
                    "future_return": 0.99,
                },
            ]
        )
        weekday = pd.DataFrame(
            [
                {
                    "symbol": "ASELS.IS",
                    "date": "2024-01-15",
                    "holding_days": 5,
                    "pattern_name": "Monday_5d_hold",
                    "status": "ok",
                    "gross_return": -0.99,
                }
            ]
        )
        technical = pd.DataFrame(
            [
                {
                    "symbol": "ASELS.IS",
                    "known_at": "2024-01-16T18:10:00+03:00",
                    "event_date": "2024-01-16",
                    "event_family": "combined",
                    "event_type": "rsi_oversold+lower_band_touch",
                    "signal_group": "combined",
                    "horizon": 5,
                    "status": "ok",
                    "forward_return": -0.99,
                }
            ]
        )
        fundamentals = pd.DataFrame(
            [
                {
                    "symbol": "ASELS.IS",
                    "disclosure_timestamp": "2024-04-15T18:30:00+03:00",
                    "metric_name": "revenue",
                    "period_end": "2024-03-31",
                    "horizon": 20,
                    "status": "ok",
                    "qoq_change": 0.10,
                    "yoy_change": pd.NA,
                    "post_disclosure_return": -0.99,
                }
            ]
        )

        signals = assemble_backtest_signals(
            sector_observations=sector,
            weekday_observations=weekday,
            technical_observations=technical,
            fundamentals_observations=fundamentals,
            preferred_horizon=5,
            fundamentals_horizon=20,
        )

        self.assertEqual(4, len(signals))
        self.assertEqual({"long"}, set(signals["direction"]))
        self.assertIn("sector_catch_up:ASELS.IS:2024-01-10:h5", set(signals["signal_id"]))
        self.assertNotIn("FROTO.IS", set(signals["symbol"]))
        self.assertTrue(signals["known_at"].str.contains(r"T18:", regex=True).any())

    def test_run_backtests_writes_measured_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            cache_dir = base / "cache"
            reports_dir = base / "reports"
            fundamentals_path = base / "fundamentals.csv"

            write_price_cache(price_frame("ASELS.IS", start=100, step=0.25), cache_dir, "ASELS.IS")
            write_price_cache(price_frame("FROTO.IS", start=200, step=0.75), cache_dir, "FROTO.IS")
            write_price_cache(price_frame("XU100.IS", start=1000, step=1.0), cache_dir, "XU100.IS")
            fundamentals_records().to_csv(fundamentals_path, index=False)

            result = run_backtests(
                universe=universe(),
                cache_dir=cache_dir,
                reports_dir=reports_dir,
                benchmark_symbol="XU100.IS",
                fundamentals_path=fundamentals_path,
                horizons=(1, 3, 5, 10, 20),
                regime_lookback_days=5,
            )

            self.assertEqual("measured", result.status)
            self.assertGreater(len(result.signals), 0)
            self.assertGreater(
                int((result.backtest.trades["status"] == "ok").sum()),
                0,
            )
            report = (reports_dir / "backtest.md").read_text(encoding="utf-8")
            self.assertIn("Measured Backtest Run", report)
            self.assertIn("Signal Counts", report)

    def test_cli_returns_nonzero_on_orchestrator_failure(self):
        with patch(
            "scripts.run_backtests.run_backtests_from_settings",
            side_effect=RuntimeError("boom"),
        ):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(1, main([]))
            self.assertIn("status=error", output.getvalue())


if __name__ == "__main__":
    unittest.main()
