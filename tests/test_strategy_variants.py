import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.settings import load_settings
from src.strategy_variants import (
    compare_strategy_variants,
    compare_strategy_variants_from_settings,
    write_strategy_variants_report,
)


def prices(symbol="AAA.IS", rows=12, start=100.0, step=1.0):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = [start + index * step for index in range(rows)]
    return pd.DataFrame(
        {
            "symbol": [symbol] * rows,
            "date": dates.date.astype(str),
            "open": [value - 0.5 for value in close],
            "close": close,
        }
    )


def signal(component, day_offset=0):
    date = pd.Timestamp("2024-01-01") + pd.offsets.BDay(day_offset)
    return pd.DataFrame(
        [
            {
                "signal_id": f"{component}-1",
                "symbol": "AAA.IS",
                "known_at": f"{date.date().isoformat()}T18:10:00+03:00",
                "horizon": 2,
                "source": component,
            }
        ]
    )


class StrategyVariantTests(unittest.TestCase):
    def test_compare_strategy_variants_marks_missing_context_variants_unavailable(self):
        result = compare_strategy_variants(
            signals_by_component={
                "technical": signal("technical"),
                "sector": signal("sector", day_offset=1),
                "fundamentals": signal("fundamentals", day_offset=2),
            },
            prices_by_symbol={"AAA.IS": prices()},
            benchmark_prices=prices("XU100.IS", start=1000, step=2),
            default_horizon=2,
        )

        status_by_variant = dict(zip(result.summary["variant"], result.summary["status"]))
        self.assertEqual("ok", status_by_variant["A"])
        self.assertEqual("ok", status_by_variant["B"])
        self.assertEqual("ok", status_by_variant["C"])
        self.assertEqual("unavailable", status_by_variant["D"])
        self.assertEqual("unavailable", status_by_variant["E"])
        missing_d = result.summary[result.summary["variant"] == "D"].iloc[0]["missing_components"]
        self.assertEqual("macro", missing_d)

    def test_all_variants_use_same_data_period_and_costs(self):
        result = compare_strategy_variants(
            signals_by_component={
                "technical": signal("technical"),
                "sector": signal("sector"),
                "fundamentals": signal("fundamentals"),
                "macro": signal("macro"),
                "news_video": signal("news_video"),
            },
            prices_by_symbol={"AAA.IS": prices(rows=15)},
            trading_cost_bps=12,
            slippage_bps=3,
            default_horizon=1,
        )

        self.assertEqual({"ok"}, set(result.summary["status"]))
        self.assertEqual({12.0}, set(result.summary["trading_cost_bps"]))
        self.assertEqual({3.0}, set(result.summary["slippage_bps"]))
        self.assertEqual({"2024-01-01"}, set(result.summary["data_start"]))
        self.assertEqual({"2024-01-19"}, set(result.summary["data_end"]))

    def test_variant_trades_include_variant_and_component_metadata(self):
        result = compare_strategy_variants(
            signals_by_component={
                "technical": signal("technical"),
                "sector": signal("sector"),
            },
            prices_by_symbol={"AAA.IS": prices()},
            default_horizon=1,
        )

        b_trades = result.trades[result.trades["variant"] == "B"]
        self.assertEqual({"technical", "sector"}, set(b_trades["component"]))
        self.assertIn("component_signal_id", b_trades.columns)

    def test_compare_strategy_variants_from_settings_uses_configured_costs(self):
        settings = load_settings()
        result = compare_strategy_variants_from_settings(
            signals_by_component={"technical": signal("technical")},
            prices_by_symbol={"AAA.IS": prices()},
            settings=settings,
        )

        row = result.summary[result.summary["variant"] == "A"].iloc[0]
        self.assertEqual(settings.backtest.trading_cost_bps, row["trading_cost_bps"])
        self.assertEqual(settings.backtest.slippage_bps, row["slippage_bps"])

    def test_write_strategy_variants_report(self):
        result = compare_strategy_variants(
            signals_by_component={"technical": signal("technical")},
            prices_by_symbol={"AAA.IS": prices()},
            default_horizon=1,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output = write_strategy_variants_report(
                result,
                Path(tmpdir) / "strategy_variants.md",
            )

            text = output.read_text(encoding="utf-8")
            self.assertIn("# Strategy Variant Comparison A-E", text)
            self.assertIn("A: technical", text)


if __name__ == "__main__":
    unittest.main()
