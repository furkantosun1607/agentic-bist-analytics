import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.research import (
    ResearchInputError,
    run_weekday_patterns,
    write_weekday_patterns_report,
)


def prices(symbol="AAA.IS", rows=35):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = [100 + index for index in range(rows)]
    return pd.DataFrame(
        {
            "symbol": [symbol] * rows,
            "date": dates.date.astype(str),
            "close": close,
        }
    )


def benchmark(rows=35):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = [100 + index * 0.25 for index in range(rows)]
    return pd.DataFrame({"date": dates.date.astype(str), "close": close})


class WeekdayPatternTest(unittest.TestCase):
    def test_weekday_patterns_generate_observations_and_summary(self):
        result = run_weekday_patterns(
            prices_by_symbol={"AAA.IS": prices()},
            benchmark_prices=benchmark(),
            holding_days=(1, 2, 5),
            trading_cost_bps=10,
            slippage_bps=5,
            regime_lookback_days=3,
            unseen_start_date="2024-02-01",
        )

        self.assertEqual((), result.errors)
        self.assertGreater(len(result.observations), 0)
        self.assertGreater(len(result.summary), 0)
        self.assertIn("weekday", set(result.observations["pattern_type"]))
        self.assertIn("multi_day", set(result.observations["pattern_type"]))
        self.assertIn("selection", set(result.observations["period_split"]))
        self.assertIn("unseen", set(result.observations["period_split"]))

    def test_cost_adjusted_return_deducts_cost_and_slippage(self):
        result = run_weekday_patterns(
            prices_by_symbol={"AAA.IS": prices(rows=10)},
            holding_days=(1,),
            trading_cost_bps=10,
            slippage_bps=5,
            regime_lookback_days=1,
        )
        ok = result.observations[result.observations["status"] == "ok"].iloc[0]

        self.assertAlmostEqual(
            ok["gross_return"] - 0.0015,
            ok["cost_adjusted_return"],
        )

    def test_summary_contains_occurrence_count_and_unconditional_baseline(self):
        result = run_weekday_patterns(
            prices_by_symbol={"AAA.IS": prices(rows=20)},
            holding_days=(1,),
            regime_lookback_days=1,
        )

        summary = result.summary.iloc[0]
        self.assertGreater(summary["occurrence_count"], 0)
        self.assertFalse(pd.isna(summary["unconditional_mean_return"]))

    def test_missing_close_is_reported_as_structured_error(self):
        result = run_weekday_patterns(
            prices_by_symbol={"AAA.IS": pd.DataFrame({"date": ["2024-01-01"]})},
            holding_days=(1,),
        )

        self.assertEqual(0, len(result.observations))
        self.assertEqual("AAA.IS", result.errors[0].scope)
        self.assertIn("missing required columns", result.errors[0].message)

    def test_invalid_holding_days_raise_clear_error(self):
        with self.assertRaisesRegex(ResearchInputError, "predefined 1-5 range"):
            run_weekday_patterns(
                prices_by_symbol={"AAA.IS": prices(rows=10)},
                holding_days=(6,),
            )

    def test_write_weekday_patterns_report(self):
        result = run_weekday_patterns(
            prices_by_symbol={"AAA.IS": prices(rows=20)},
            holding_days=(1, 2),
            regime_lookback_days=1,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_weekday_patterns_report(
                result,
                Path(tmpdir) / "weekday_patterns.md",
            )

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Weekday And Multi-Day Pattern Report", text)
            self.assertIn("Multiple-testing note", text)


if __name__ == "__main__":
    unittest.main()
