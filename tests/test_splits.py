import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.settings import load_settings
from src.splits import (
    SplitInputError,
    apply_split_and_regime_labels,
    build_market_regime_frame,
    label_period_split,
    summarize_unseen_stability,
    write_split_regime_report,
)


def observations():
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=6, freq="B").date.astype(str),
            "close": [100, 102, 104, 101, 99, 103],
            "strategy": ["a", "a", "a", "a", "a", "a"],
            "status": ["ok", "ok", "ok", "ok", "ok", "ok"],
            "return": [0.02, 0.03, 0.01, -0.04, -0.02, -0.01],
        }
    )


def benchmark():
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=6, freq="B").date.astype(str),
            "close": [1000, 1010, 1020, 1005, 990, 1001],
        }
    )


class SplitTests(unittest.TestCase):
    def test_label_period_split_marks_selection_and_unseen(self):
        labeled = label_period_split(observations(), unseen_start_date="2024-01-04")

        self.assertEqual(["selection", "selection", "selection"], list(labeled["period_split"].head(3)))
        self.assertEqual(["unseen", "unseen", "unseen"], list(labeled["period_split"].tail(3)))

    def test_none_unseen_start_keeps_full_sample_label(self):
        labeled = label_period_split(observations(), unseen_start_date=None)

        self.assertEqual({"full_sample"}, set(labeled["period_split"]))

    def test_market_regime_frame_uses_benchmark_returns(self):
        regimes = build_market_regime_frame(benchmark(), lookback_days=1)

        self.assertEqual("unknown", regimes.iloc[0]["market_regime"])
        self.assertEqual("rising", regimes.iloc[1]["market_regime"])
        self.assertEqual("falling", regimes.iloc[3]["market_regime"])

    def test_apply_split_and_regime_labels_combines_both_labels(self):
        labeled = apply_split_and_regime_labels(
            observations(),
            unseen_start_date="2024-01-04",
            benchmark_prices=benchmark(),
            lookback_days=1,
        )

        self.assertIn("period_split", labeled.columns)
        self.assertIn("market_regime", labeled.columns)
        self.assertIn("regime_return", labeled.columns)
        self.assertEqual("unseen", labeled.iloc[3]["period_split"])
        self.assertEqual("falling", labeled.iloc[3]["market_regime"])

    def test_stability_summary_compares_selection_and_unseen_returns(self):
        labeled = label_period_split(observations(), unseen_start_date="2024-01-04")

        summary = summarize_unseen_stability(
            labeled,
            group_columns=["strategy"],
            return_column="return",
        )

        row = summary.iloc[0]
        self.assertEqual(3, row["selection_count"])
        self.assertEqual(3, row["unseen_count"])
        self.assertGreater(row["selection_average_return"], 0)
        self.assertLess(row["unseen_average_return"], 0)
        self.assertEqual("sign_flip", row["stability_label"])

    def test_stability_summary_requires_period_split(self):
        with self.assertRaisesRegex(SplitInputError, "missing required columns"):
            summarize_unseen_stability(
                observations(),
                group_columns=["strategy"],
                return_column="return",
            )

    def test_settings_include_experiment_split_defaults(self):
        settings = load_settings()

        self.assertIsNone(settings.experiment.unseen_start_date)
        self.assertEqual(20, settings.experiment.regime_lookback_days)

    def test_write_split_regime_report(self):
        labeled = label_period_split(observations(), unseen_start_date="2024-01-04")
        summary = summarize_unseen_stability(
            labeled,
            group_columns=["strategy"],
            return_column="return",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_split_regime_report(summary, Path(tmpdir) / "splits.md")

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Unseen Period And Regime Split Report", text)
            self.assertIn("Stability Summary", text)


if __name__ == "__main__":
    unittest.main()
