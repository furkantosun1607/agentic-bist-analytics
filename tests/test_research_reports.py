import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.run_research_reports import main
from src.data import UniverseMember, write_price_cache
from src.research_reports import (
    build_events_from_prices,
    load_cached_universe_prices,
    run_research_reports,
)


def price_frame(symbol, start=100.0, rows=120, step=0.5):
    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = pd.Series([start + index * step for index in range(rows)])
    return pd.DataFrame(
        {
            "symbol": [symbol] * rows,
            "date": dates.date.astype(str),
            "open": close - 0.2,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "adj_close": close,
            "volume": [1000 + index * 10 for index in range(rows)],
            "source": ["test"] * rows,
            "download_timestamp": ["2026-09-25T00:00:00+00:00"] * rows,
        }
    )


def fundamentals_frame():
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
            }
        ]
    )


def universe():
    return [
        UniverseMember("ASELS", "ASELS.IS", "Technology / Defense"),
        UniverseMember("FROTO", "FROTO.IS", "Technology / Defense"),
    ]


class ResearchReportsTest(unittest.TestCase):
    def test_load_cached_universe_prices_reports_missing_symbols(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            write_price_cache(price_frame("ASELS.IS"), tmpdir, "ASELS.IS")

            prices, missing = load_cached_universe_prices(universe(), tmpdir)

            self.assertEqual(["FROTO.IS"], missing)
            self.assertEqual(["ASELS.IS"], list(prices))

    def test_build_events_from_prices_returns_symbol_event_map(self):
        events_by_symbol, errors = build_events_from_prices(
            {"ASELS.IS": price_frame("ASELS.IS", rows=90)}
        )

        self.assertEqual([], errors)
        self.assertIn("ASELS.IS", events_by_symbol)

    def test_run_research_reports_writes_all_reports_and_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            cache_dir = base / "cache"
            reports_dir = base / "reports"
            fundamentals_path = base / "fundamentals.csv"

            write_price_cache(price_frame("ASELS.IS", start=100), cache_dir, "ASELS.IS")
            write_price_cache(price_frame("FROTO.IS", start=200, step=0.4), cache_dir, "FROTO.IS")
            write_price_cache(price_frame("XU100.IS", start=1000, step=1.0), cache_dir, "XU100.IS")
            fundamentals_frame().to_csv(fundamentals_path, index=False)

            result = run_research_reports(
                universe=universe(),
                cache_dir=cache_dir,
                reports_dir=reports_dir,
                benchmark_symbol="XU100.IS",
                fundamentals_path=fundamentals_path,
                horizons=(1, 3, 5, 10, 20),
                regime_lookback_days=5,
            )

            self.assertEqual(4, len(result.reports))
            self.assertEqual((), result.missing_price_symbols)
            self.assertTrue((reports_dir / "sector_catch_up.md").exists())
            self.assertTrue((reports_dir / "weekday_patterns.md").exists())
            self.assertTrue((reports_dir / "technical_reversals.md").exists())
            self.assertTrue((reports_dir / "quarterly_fundamentals.md").exists())
            self.assertTrue((reports_dir / "research_run_status.md").exists())
            self.assertIn(
                "Run Metadata",
                (reports_dir / "sector_catch_up.md").read_text(encoding="utf-8"),
            )

    def test_cli_returns_nonzero_when_reports_are_not_all_measured(self):
        with patch(
            "scripts.run_research_reports.run_research_reports_from_settings",
            side_effect=RuntimeError("boom"),
        ):
            with redirect_stdout(StringIO()):
                self.assertEqual(1, main([]))


if __name__ == "__main__":
    unittest.main()
