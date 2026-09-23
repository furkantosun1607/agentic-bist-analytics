import unittest

import pandas as pd

from src.events import (
    EVENT_COLUMNS,
    detect_all_events,
    detect_bollinger_events,
    detect_rsi_events,
    detect_support_resistance_events,
)


def event_frame():
    dates = pd.date_range("2024-01-01", periods=8, freq="B").date.astype(str)
    return pd.DataFrame(
        {
            "symbol": ["ASELS.IS"] * 8,
            "date": dates,
            "close": [10.0, 9.0, 8.0, 9.5, 11.0, 12.0, 10.5, 9.0],
            "bb_lower": [9.0] * 8,
            "bb_middle": [10.0] * 8,
            "bb_upper": [11.5] * 8,
            "rsi_14": [45.0, 28.0, 24.0, 35.0, 72.0, 78.0, 65.0, 40.0],
            "supertrend_direction": [1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, -1.0],
            "kama_10": [10.2, 9.8, 8.6, 9.0, 10.2, 11.5, 11.0, 10.0],
            "ichimoku_conversion": [9.0, 9.2, 9.4, 10.2, 10.8, 11.0, 10.2, 9.5],
            "ichimoku_base": [9.5, 9.4, 9.3, 9.8, 10.6, 11.2, 10.4, 9.8],
            "ichimoku_span_a": [10.5] * 8,
            "ichimoku_span_b": [11.0] * 8,
            "support": [8.95] * 8,
            "resistance": [12.05] * 8,
        }
    )


class EventDetectorTest(unittest.TestCase):
    def test_bollinger_events_use_standard_schema_and_known_at_timestamp(self):
        events = detect_bollinger_events(event_frame())

        self.assertEqual(list(EVENT_COLUMNS), list(events.columns))
        self.assertIn("lower_band_touch", set(events["event_type"]))
        self.assertIn("upper_band_touch", set(events["event_type"]))
        self.assertTrue(events["known_at"].str.endswith("T18:10:00+03:00").all())

    def test_rsi_events_include_peak_trough_and_threshold_exits(self):
        events = detect_rsi_events(event_frame())

        self.assertIn("oversold_trough", set(events["event_type"]))
        self.assertIn("oversold_exit", set(events["event_type"]))
        self.assertIn("overbought_peak", set(events["event_type"]))
        self.assertIn("overbought_exit", set(events["event_type"]))

    def test_support_resistance_touches_use_tolerance(self):
        events = detect_support_resistance_events(event_frame(), tolerance=0.01)

        self.assertIn("support_touch", set(events["event_type"]))
        self.assertIn("resistance_touch", set(events["event_type"]))

    def test_detect_all_events_collects_events_without_errors(self):
        result = detect_all_events(event_frame())

        self.assertEqual((), result.errors)
        self.assertGreater(len(result.events), 0)
        self.assertEqual(list(EVENT_COLUMNS), list(result.events.columns))

    def test_detect_all_events_reports_detector_errors(self):
        broken = event_frame().drop(columns=["bb_lower", "bb_middle", "bb_upper"])

        result = detect_all_events(broken)

        self.assertGreater(len(result.events), 0)
        self.assertIn("bollinger", [error.detector for error in result.errors])
        self.assertIn("missing required columns", result.errors[0].message)


if __name__ == "__main__":
    unittest.main()
