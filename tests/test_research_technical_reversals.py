import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.research import (
    ResearchInputError,
    run_technical_reversals,
    write_technical_reversals_report,
)


def prices(symbol="AAA.IS", closes=None):
    if closes is None:
        closes = [100, 101, 103, 102, 106, 108, 107, 110, 112, 111, 115, 118]
    dates = pd.date_range("2024-01-01", periods=len(closes), freq="B")
    return pd.DataFrame(
        {
            "symbol": [symbol] * len(closes),
            "date": dates.date.astype(str),
            "close": closes,
        }
    )


def events():
    return pd.DataFrame(
        {
            "symbol": ["AAA.IS", "AAA.IS", "AAA.IS"],
            "event_family": ["rsi", "bollinger", "supertrend"],
            "event_type": ["oversold_exit", "lower_band_touch", "flip_up"],
            "event_date": ["2024-01-01", "2024-01-01", "2024-01-05"],
            "known_at": [
                "2024-01-01T18:10:00+03:00",
                "2024-01-01T18:10:00+03:00",
                "2024-01-05T18:10:00+03:00",
            ],
        }
    )


class TechnicalReversalTest(unittest.TestCase):
    def test_reversal_uses_next_trading_day_entry(self):
        result = run_technical_reversals(
            prices_by_symbol={"AAA.IS": prices()},
            events_by_symbol={"AAA.IS": events().iloc[:1]},
            horizons=(1,),
            regime_lookback_days=1,
        )

        row = result.observations.iloc[0]
        self.assertEqual((), result.errors)
        self.assertEqual("2024-01-02", row["entry_date"])
        self.assertEqual(101.0, row["entry_close"])
        self.assertEqual("2024-01-03", row["exit_date"])
        self.assertGreater(row["forward_return"], 0)
        self.assertTrue(bool(row["bounce"]))

    def test_combined_signal_is_created_for_same_day_events(self):
        result = run_technical_reversals(
            prices_by_symbol={"AAA.IS": prices()},
            events_by_symbol={"AAA.IS": events()},
            horizons=(1, 3),
            regime_lookback_days=1,
        )

        self.assertIn("combined", set(result.observations["signal_group"]))
        combined = result.observations[result.observations["signal_group"] == "combined"]
        self.assertEqual({1, 3}, set(combined["horizon"]))
        self.assertIn("combined", set(result.summary["event_family"]))

    def test_summary_reports_bounce_and_failure_counts(self):
        result = run_technical_reversals(
            prices_by_symbol={"AAA.IS": prices(closes=[100, 90, 89, 88, 87, 86, 85])},
            events_by_symbol={"AAA.IS": events().iloc[:1]},
            horizons=(1,),
            regime_lookback_days=1,
        )

        summary = result.summary.iloc[0]
        self.assertEqual(1, summary["event_count"])
        self.assertEqual(0, summary["bounce_count"])
        self.assertEqual(1, summary["failure_count"])
        self.assertEqual(0, summary["bounce_rate"])

    def test_missing_price_history_is_structured_error(self):
        result = run_technical_reversals(
            prices_by_symbol={},
            events_by_symbol={"AAA.IS": events()},
            horizons=(1,),
        )

        self.assertEqual(0, len(result.observations))
        self.assertEqual("AAA.IS", result.errors[0].scope)
        self.assertIn("missing price history", result.errors[0].message)

    def test_invalid_horizon_raises_clear_error(self):
        with self.assertRaisesRegex(ResearchInputError, "horizons must be positive"):
            run_technical_reversals(
                prices_by_symbol={"AAA.IS": prices()},
                events_by_symbol={"AAA.IS": events()},
                horizons=(0,),
            )

    def test_write_technical_reversals_report(self):
        result = run_technical_reversals(
            prices_by_symbol={"AAA.IS": prices()},
            events_by_symbol={"AAA.IS": events()},
            horizons=(1,),
            regime_lookback_days=1,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_technical_reversals_report(
                result,
                Path(tmpdir) / "technical_reversals.md",
            )

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Technical Reversal Report", text)
            self.assertIn("Combined signals", text)


if __name__ == "__main__":
    unittest.main()
