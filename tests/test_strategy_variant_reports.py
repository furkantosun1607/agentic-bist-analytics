import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.run_strategy_variants import main
from src.data import UniverseMember, write_price_cache
from src.strategy_variant_reports import (
    assemble_strategy_component_signals,
    run_strategy_variants,
)


def signals():
    return pd.DataFrame(
        [
            {
                "signal_id": "technical-1",
                "symbol": "ASELS.IS",
                "known_at": "2024-01-02T18:10:00+03:00",
                "direction": "long",
                "horizon": 5,
                "source": "technical_reversal_fixed",
            },
            {
                "signal_id": "sector-1",
                "symbol": "ASELS.IS",
                "known_at": "2024-01-03T18:10:00+03:00",
                "direction": "long",
                "horizon": 5,
                "source": "sector_catch_up_laggard",
            },
            {
                "signal_id": "fundamentals-1",
                "symbol": "ASELS.IS",
                "known_at": "2024-04-15T18:30:00+03:00",
                "direction": "long",
                "horizon": 20,
                "source": "fundamentals_positive_change",
            },
            {
                "signal_id": "weekday-1",
                "symbol": "ASELS.IS",
                "known_at": "2024-01-08T18:10:00+03:00",
                "direction": "long",
                "horizon": 5,
                "source": "weekday_monday_fixed",
            },
        ]
    )


def price_frame(symbol, start=100.0, rows=560, step=0.1):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = pd.Series([start + index * step for index in range(rows)])
    return pd.DataFrame(
        {
            "symbol": [symbol] * rows,
            "date": dates.date.astype(str),
            "open": close - 0.1,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "adj_close": close,
            "volume": [1000 + index for index in range(rows)],
            "source": ["test"] * rows,
            "download_timestamp": ["2026-09-25T00:00:00+00:00"] * rows,
        }
    )


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
            },
            {
                "ticker": "ASELS",
                "period_end": "2024-06-30",
                "period_type": "quarterly",
                "disclosure_timestamp": "2024-08-09T18:30:00+03:00",
                "download_timestamp": "2024-08-10T09:00:00+03:00",
                "source": "test",
                "currency": "TRY",
                "revenue": 120.0,
                "gross_profit": 50.0,
                "operating_profit": 38.0,
                "net_income": 25.0,
                "total_assets": 520.0,
                "total_debt": 95.0,
                "operating_cash_flow": 30.0,
                "free_cash_flow": 20.0,
            }
        ]
    )


def rss_context(path):
    pd.DataFrame(
        [
            {
                "entity_type": "ticker",
                "entity_id": "ASELS",
                "decision_timestamp": "2024-04-20T12:00:00+00:00",
                "lookback_days": 7,
                "news_count": 2,
                "source_count": 2,
                "latest_news_timestamp": "2024-04-19T09:00:00+00:00",
                "evidence_urls": "https://example.com/a;https://example.com/b",
                "matched_terms": "ASELS",
            }
        ]
    ).to_csv(path, index=False)


class StrategyVariantReportsTest(unittest.TestCase):
    def test_assemble_strategy_component_signals_excludes_weekday_and_rss(self):
        components = assemble_strategy_component_signals(signals())

        self.assertEqual({"technical", "sector", "fundamentals"}, set(components))
        self.assertNotIn("weekday", components)
        self.assertEqual("technical", components["technical"].iloc[0]["source"])

    def test_run_strategy_variants_writes_partial_measured_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            cache_dir = base / "cache"
            reports_dir = base / "reports"
            fundamentals_path = base / "fundamentals.csv"
            rss_path = base / "news_context.csv"

            write_price_cache(price_frame("ASELS.IS", start=100, step=0.0), cache_dir, "ASELS.IS")
            write_price_cache(price_frame("FROTO.IS", start=200, step=0.5), cache_dir, "FROTO.IS")
            write_price_cache(price_frame("XU100.IS", start=1000, step=0.5), cache_dir, "XU100.IS")
            fundamentals_records().to_csv(fundamentals_path, index=False)
            rss_context(rss_path)

            result = run_strategy_variants(
                universe=[
                    UniverseMember("ASELS", "ASELS.IS", "Technology / Defense"),
                    UniverseMember("FROTO", "FROTO.IS", "Technology / Defense"),
                ],
                cache_dir=cache_dir,
                reports_dir=reports_dir,
                benchmark_symbol="XU100.IS",
                fundamentals_path=fundamentals_path,
                rss_context_path=rss_path,
                horizons=(1, 3, 5, 10, 20),
                regime_lookback_days=5,
            )

            self.assertEqual("measured_partial", result.status)
            status_by_variant = dict(
                zip(result.comparison.summary["variant"], result.comparison.summary["status"])
            )
            self.assertEqual("ok", status_by_variant["A"])
            self.assertEqual("ok", status_by_variant["B"])
            self.assertEqual("ok", status_by_variant["C"])
            self.assertEqual("unavailable", status_by_variant["D"])
            self.assertEqual("unavailable", status_by_variant["E"])
            text = (reports_dir / "strategy_variants.md").read_text(encoding="utf-8")
            self.assertIn("Measured Variant Run", text)
            self.assertIn("RSS context is included only as Variant E evidence metadata", text)

    def test_cli_returns_nonzero_on_orchestrator_failure(self):
        with patch(
            "scripts.run_strategy_variants.run_strategy_variants_from_settings",
            side_effect=RuntimeError("boom"),
        ):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(1, main([]))
            self.assertIn("status=error", output.getvalue())


if __name__ == "__main__":
    unittest.main()
