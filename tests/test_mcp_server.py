import unittest

import pandas as pd

from src.data import UniverseMember
from src.mcp_server import call_tool, list_tools


def prices(symbol="AAA.IS", rows=80, start=100.0, step=1.0):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = [start + index * step for index in range(rows)]
    return pd.DataFrame(
        {
            "symbol": [symbol] * rows,
            "date": dates.date.astype(str),
            "open": [value - 0.25 for value in close],
            "high": [value + 1 for value in close],
            "low": [value - 1 for value in close],
            "close": close,
            "adj_close": close,
            "volume": [1000 + index for index in range(rows)],
            "source": ["unit_test"] * rows,
            "download_timestamp": ["2024-05-01T12:00:00+03:00"] * rows,
        }
    )


def context_rows():
    return pd.DataFrame(
        [
            {
                "context_id": "macro-1",
                "context_type": "macro",
                "scope": "macro",
                "indicator": "usd_try",
                "value": 32.0,
                "unit": "TRY",
                "observed_period_start": "2024-01-01",
                "observed_period_end": "2024-01-01",
                "publication_timestamp": "2024-01-01T12:00:00+03:00",
                "download_timestamp": "2024-01-01T13:00:00+03:00",
                "source": "tcmb",
                "source_access": "public",
            }
        ]
    )


class McpServerTests(unittest.TestCase):
    def test_list_tools_exposes_required_tool_set(self):
        names = {tool.name for tool in list_tools()}

        self.assertIn("market_history", names)
        self.assertIn("indicators_events", names)
        self.assertIn("sector_ranking", names)
        self.assertIn("weekday_test", names)
        self.assertIn("point_in_time_fundamentals", names)
        self.assertIn("context", names)
        self.assertIn("backtest", names)
        self.assertIn("data_quality", names)
        self.assertIn("evidence_bundle", names)

    def test_unknown_tool_returns_error_response(self):
        response = call_tool("missing_tool", {})

        self.assertEqual("error", response.status)
        self.assertIn("unknown tool", response.errors[0])

    def test_market_history_tool_summarizes_price_frames(self):
        response = call_tool(
            "market_history",
            {"prices_by_symbol": {"AAA.IS": prices("AAA.IS", rows=5)}},
        )

        self.assertEqual("ok", response.status)
        self.assertEqual(1, response.data["symbol_count"])
        self.assertEqual("AAA.IS", response.data["symbols"][0]["symbol"])

    def test_indicators_events_tool_returns_latest_indicators_and_events(self):
        response = call_tool(
            "indicators_events",
            {"prices": prices("AAA.IS"), "symbol": "AAA.IS"},
        )

        self.assertEqual("ok", response.status)
        self.assertEqual("AAA.IS", response.data["symbol"])
        self.assertIn("rsi_14", response.data["latest_indicators"])
        self.assertIn("event_count", response.data)

    def test_sector_ranking_tool_runs_catch_up_analysis(self):
        response = call_tool(
            "sector_ranking",
            {
                "prices_by_symbol": {
                    "AAA.IS": prices("AAA.IS", rows=8, start=100, step=1),
                    "BBB.IS": prices("BBB.IS", rows=8, start=100, step=2),
                },
                "universe": [
                    UniverseMember("AAA", "AAA.IS", "Technology"),
                    UniverseMember("BBB", "BBB.IS", "Technology"),
                ],
                "lookback_days": 1,
                "horizons": (1,),
            },
        )

        self.assertEqual("ok", response.status)
        self.assertGreater(response.data["observation_count"], 0)

    def test_weekday_test_tool_returns_summary(self):
        response = call_tool(
            "weekday_test",
            {
                "prices_by_symbol": {"AAA.IS": prices("AAA.IS", rows=20)},
                "holding_days": (1, 2),
                "regime_lookback_days": 1,
            },
        )

        self.assertEqual("ok", response.status)
        self.assertGreater(response.data["observation_count"], 0)
        self.assertIsInstance(response.data["summary"], list)

    def test_context_tool_filters_by_decision_timestamp(self):
        response = call_tool(
            "context",
            {
                "context_records": context_rows(),
                "decision_timestamp": "2024-01-01T13:30:00+03:00",
            },
        )

        self.assertEqual("ok", response.status)
        self.assertEqual(1, response.data["record_count"])
        self.assertEqual("ANALYSIS_SAFE", response.data["gate_status"])

    def test_backtest_tool_runs_structured_backtest(self):
        signals = pd.DataFrame(
            [
                {
                    "signal_id": "sig-1",
                    "symbol": "AAA.IS",
                    "known_at": "2024-01-01T18:10:00+03:00",
                    "horizon": 2,
                }
            ]
        )

        response = call_tool(
            "backtest",
            {
                "signals": signals,
                "prices_by_symbol": {"AAA.IS": prices("AAA.IS", rows=10)},
            },
        )

        self.assertEqual("ok", response.status)
        self.assertEqual(1, response.data["trade_count"])
        self.assertEqual(1, len(response.data["summary"]))

    def test_data_quality_tool_flags_future_outcome_features(self):
        response = call_tool(
            "data_quality",
            {"feature_columns": ["rsi_14", "future_return"]},
        )

        self.assertEqual("warning", response.status)
        self.assertEqual("ANALYSIS_UNSAFE", response.data["gate_status"])
        self.assertIn("prices_by_symbol not provided", response.warnings)

    def test_evidence_bundle_tool_builds_source_linked_records(self):
        records = pd.DataFrame(
            [
                {
                    "signal_id": "sig-1",
                    "source": "unit_test",
                    "known_at": "2024-01-01T18:10:00+03:00",
                    "score": 0.42,
                }
            ]
        )

        response = call_tool(
            "evidence_bundle",
            {"records": records, "feature_columns": ["score"]},
        )

        self.assertEqual("ok", response.status)
        self.assertEqual(1, response.data["evidence_count"])
        self.assertIn("evidence_hash", response.data)
        self.assertEqual("ANALYSIS_SAFE", response.data["quality_gate"]["gate_status"])
        self.assertEqual(0.42, response.data["evidence"][0]["observed_features"]["score"])


if __name__ == "__main__":
    unittest.main()
