import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.data import UniverseMember
from src.research import (
    ResearchInputError,
    run_sector_catch_up,
    write_sector_catch_up_report,
)


def prices(symbol, closes):
    dates = pd.date_range("2024-01-01", periods=len(closes), freq="B")
    return pd.DataFrame(
        {
            "symbol": [symbol] * len(closes),
            "date": dates.date.astype(str),
            "close": closes,
        }
    )


def universe():
    return [
        UniverseMember("AAA", "AAA.IS", "Sector A"),
        UniverseMember("BBB", "BBB.IS", "Sector A"),
        UniverseMember("CCC", "CCC.IS", "Sector B"),
    ]


class SectorCatchUpTest(unittest.TestCase):
    def test_sector_catch_up_marks_laggard_and_future_relative_return(self):
        result = run_sector_catch_up(
            prices_by_symbol={
                "AAA.IS": prices("AAA.IS", [100, 90, 95, 98, 102, 105]),
                "BBB.IS": prices("BBB.IS", [100, 110, 111, 112, 113, 114]),
            },
            universe=universe()[:2],
            lookback_days=1,
            horizons=(2,),
        )

        self.assertEqual((), result.errors)
        eligible = result.observations[
            (result.observations["symbol"] == "AAA.IS")
            & (result.observations["date"] == "2024-01-02")
        ].iloc[0]

        self.assertEqual("ok", eligible["status"])
        self.assertTrue(bool(eligible["is_laggard"]))
        self.assertGreater(eligible["future_relative_return"], 0)
        self.assertFalse(bool(eligible["false_positive"]))

    def test_single_stock_sector_is_insufficient_peers(self):
        result = run_sector_catch_up(
            prices_by_symbol={
                "CCC.IS": prices("CCC.IS", [50, 51, 52, 53]),
            },
            universe=universe(),
            lookback_days=1,
            horizons=(1,),
        )

        statuses = set(result.observations["status"])
        self.assertIn("insufficient_peers", statuses)

    def test_peer_median_alignment_survives_sorted_non_range_index(self):
        result = run_sector_catch_up(
            prices_by_symbol={
                "BBB.IS": prices("BBB.IS", [100, 110, 111, 112, 113, 114]),
                "AAA.IS": prices("AAA.IS", [100, 90, 95, 98, 102, 105]),
            },
            universe=universe()[:2],
            lookback_days=1,
            horizons=(2,),
        )

        eligible = result.observations[result.observations["status"] == "ok"]

        self.assertFalse(eligible.empty)
        self.assertFalse(eligible["peer_median_future_return"].isna().any())

    def test_missing_symbol_column_error_is_structured(self):
        result = run_sector_catch_up(
            prices_by_symbol={
                "AAA.IS": pd.DataFrame({"date": ["2024-01-01"], "open": [1.0]}),
            },
            universe=universe(),
            lookback_days=1,
            horizons=(1,),
        )

        self.assertEqual(0, len(result.observations))
        self.assertEqual("sector_catch_up", result.errors[0].scope)
        self.assertIn("missing required columns", result.errors[0].message)

    def test_invalid_horizon_raises_clear_error(self):
        with self.assertRaisesRegex(ResearchInputError, "horizons must be positive"):
            run_sector_catch_up(
                prices_by_symbol={"AAA.IS": prices("AAA.IS", [1, 2, 3])},
                universe=universe(),
                horizons=(0,),
            )

    def test_write_sector_catch_up_report(self):
        result = run_sector_catch_up(
            prices_by_symbol={
                "AAA.IS": prices("AAA.IS", [100, 90, 95, 98, 102, 105]),
                "BBB.IS": prices("BBB.IS", [100, 110, 111, 112, 113, 114]),
            },
            universe=universe()[:2],
            lookback_days=1,
            horizons=(2,),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_sector_catch_up_report(
                result,
                Path(tmpdir) / "sector_catch_up.md",
                lookback_days=1,
            )

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Sector Catch-Up Report", text)
            self.assertIn("Status Counts", text)


if __name__ == "__main__":
    unittest.main()
