import unittest

import pandas as pd

from src.indicators import (
    add_all_indicators,
    atr,
    bollinger_bands,
    ema,
    ichimoku,
    kama,
    macd,
    rsi,
    sma,
    supertrend,
    support_resistance,
    true_range,
    volume_indicators,
)


def sample_prices(rows=80):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = pd.Series([100 + index * 0.5 for index in range(rows)])
    return pd.DataFrame(
        {
            "symbol": ["ASELS.IS"] * rows,
            "date": dates.date.astype(str),
            "open": close - 0.2,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "adj_close": close,
            "volume": [1000 + index * 10 for index in range(rows)],
            "source": ["test"] * rows,
            "download_timestamp": ["2024-05-01T00:00:00+00:00"] * rows,
        }
    )


class IndicatorTest(unittest.TestCase):
    def test_sma_and_ema_keep_expected_nan_window_behavior(self):
        prices = sample_prices(25)
        close = prices["close"]

        self.assertTrue(pd.isna(sma(close, 20).iloc[18]))
        self.assertAlmostEqual(close.iloc[:20].mean(), sma(close, 20).iloc[19])
        self.assertTrue(pd.isna(ema(close, 20).iloc[18]))
        self.assertFalse(pd.isna(ema(close, 20).iloc[19]))

    def test_kama_and_rsi_return_series_on_price_index(self):
        prices = sample_prices(40)
        close = prices["close"]

        kama_values = kama(close, window=10)
        rsi_values = rsi(close, window=14)

        self.assertEqual(len(close), len(kama_values))
        self.assertTrue(pd.isna(kama_values.iloc[9]))
        self.assertFalse(pd.isna(kama_values.iloc[11]))
        self.assertGreaterEqual(rsi_values.dropna().iloc[-1], 0)
        self.assertLessEqual(rsi_values.dropna().iloc[-1], 100)

    def test_macd_and_bollinger_columns(self):
        prices = sample_prices(60)
        close = prices["close"]

        self.assertEqual(
            ["macd", "macd_signal", "macd_histogram"],
            list(macd(close).columns),
        )
        self.assertEqual(
            ["bb_lower", "bb_middle", "bb_upper", "bb_width"],
            list(bollinger_bands(close).columns),
        )
        bands = bollinger_bands(close).dropna()
        self.assertTrue((bands["bb_upper"] >= bands["bb_middle"]).all())
        self.assertTrue((bands["bb_middle"] >= bands["bb_lower"]).all())

    def test_true_range_and_atr(self):
        prices = sample_prices(20)

        tr = true_range(prices)
        atr_values = atr(prices, window=14)

        self.assertEqual(len(prices), len(tr))
        self.assertAlmostEqual(2.0, tr.iloc[0])
        self.assertTrue(pd.isna(atr_values.iloc[12]))
        self.assertFalse(pd.isna(atr_values.iloc[13]))

    def test_supertrend_ichimoku_support_and_volume_shapes(self):
        prices = sample_prices(80)

        self.assertEqual(4, len(supertrend(prices).columns))
        self.assertEqual(5, len(ichimoku(prices).columns))
        self.assertEqual(4, len(support_resistance(prices).columns))
        self.assertEqual(2, len(volume_indicators(prices).columns))

    def test_add_all_indicators_appends_expected_columns(self):
        enriched = add_all_indicators(sample_prices(80))

        for column in (
            "sma_20",
            "ema_20",
            "kama_10",
            "rsi_14",
            "macd",
            "bb_lower",
            "atr_14",
            "supertrend",
            "ichimoku_conversion",
            "support",
            "relative_volume",
        ):
            self.assertIn(column, enriched.columns)

        self.assertEqual(80, len(enriched))


if __name__ == "__main__":
    unittest.main()
