import unittest

import pandas as pd

from src.harness import (
    EDUCATIONAL_OUTPUT_LABELS,
    HARNESS_STATES,
    AnalysisHarness,
    create_harness,
)


def prices(rows=5):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = [100 + index for index in range(rows)]
    return pd.DataFrame(
        {
            "symbol": ["AAA.IS"] * rows,
            "date": dates.date.astype(str),
            "open": [value - 0.25 for value in close],
            "high": [value + 1 for value in close],
            "low": [value - 1 for value in close],
            "close": close,
            "adj_close": close,
            "volume": [1000] * rows,
            "source": ["unit_test"] * rows,
            "download_timestamp": ["2024-05-01T12:00:00+03:00"] * rows,
        }
    )


class HarnessTests(unittest.TestCase):
    def test_harness_starts_at_select_universe(self):
        harness = create_harness()

        self.assertEqual("select_universe", harness.current_state())
        self.assertEqual((), harness.permitted_tools())
        self.assertEqual(HARNESS_STATES[0], harness.snapshot()["state"])

    def test_advance_enforces_state_order(self):
        harness = AnalysisHarness()

        blocked = harness.advance(expected_state="run_analyses")
        advanced = harness.advance(expected_state="select_universe")

        self.assertEqual("error", blocked.status)
        self.assertIn("current state is select_universe", blocked.errors[0])
        self.assertEqual("ok", advanced.status)
        self.assertEqual("load_validate", harness.current_state())

    def test_tool_call_is_blocked_when_not_permitted(self):
        harness = AnalysisHarness()

        result = harness.call_tool(
            "backtest",
            {"signals": pd.DataFrame(), "prices_by_symbol": {"AAA.IS": prices()}},
        )

        self.assertEqual("error", result.status)
        self.assertIn("not permitted", result.errors[0])
        self.assertEqual("tool_blocked", harness.events[-1].event_type)

    def test_permitted_tool_calls_underlying_registry(self):
        harness = AnalysisHarness()
        harness.advance(expected_state="select_universe")

        result = harness.call_tool(
            "market_history",
            {"prices_by_symbol": {"AAA.IS": prices()}},
        )

        self.assertEqual("ok", result.status)
        self.assertIsNotNone(result.response)
        self.assertEqual(1, result.response.data["symbol_count"])
        self.assertEqual("tool_called", harness.events[-1].event_type)

    def test_output_label_can_only_be_set_in_explain_state(self):
        harness = AnalysisHarness()

        early = harness.set_output_label("WATCH")
        for state in HARNESS_STATES[1:HARNESS_STATES.index("explain") + 1]:
            harness.advance()

        accepted = harness.set_output_label("watch")
        rejected = harness.set_output_label("BUY")

        self.assertEqual("error", early.status)
        self.assertEqual("ok", accepted.status)
        self.assertEqual("WATCH", harness.output_label)
        self.assertEqual("error", rejected.status)
        self.assertIn("WATCH", EDUCATIONAL_OUTPUT_LABELS)

    def test_human_review_and_save_require_correct_state(self):
        harness = AnalysisHarness()
        for _ in range(HARNESS_STATES.index("explain")):
            harness.advance()
        harness.set_output_label("INVESTIGATE")
        harness.advance(expected_state="explain")

        review = harness.record_human_review("accept")
        blocked_save = harness.save_decision()
        harness.advance(expected_state="human_review")
        saved = harness.save_decision()

        self.assertEqual("ok", review.status)
        self.assertEqual("error", blocked_save.status)
        self.assertEqual("ok", saved.status)
        self.assertTrue(harness.saved)

    def test_save_requires_output_label_and_review(self):
        harness = AnalysisHarness(state="save_decision")

        result = harness.save_decision()

        self.assertEqual("error", result.status)
        self.assertIn("output label", result.errors[0])

    def test_snapshot_contains_event_log_and_permitted_tools(self):
        harness = AnalysisHarness()
        harness.advance()
        snapshot = harness.snapshot()

        self.assertEqual("load_validate", snapshot["state"])
        self.assertIn("market_history", snapshot["permitted_tools"])
        self.assertEqual(1, len(snapshot["events"]))


if __name__ == "__main__":
    unittest.main()
