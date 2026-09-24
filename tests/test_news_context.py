import csv
import tempfile
import unittest
from pathlib import Path

from src.news_aliases import MatchedNewsItem, write_matched_news_jsonl
from src.news_context import (
    NEWS_CONTEXT_COLUMNS,
    build_news_context,
    build_news_context_from_cache,
)


def matched_item(
    title: str,
    published_timestamp: str | None,
    linked_entities: tuple[str, ...],
    source_id: str = "source_a",
    url: str = "https://example.com/news",
) -> MatchedNewsItem:
    return MatchedNewsItem(
        source_id=source_id,
        title=title,
        url=url,
        summary="summary",
        published_timestamp=published_timestamp,
        fetched_timestamp="2026-09-24T10:05:00+00:00",
        language="tr",
        category="economy",
        source_access="rss",
        raw_source_url="https://example.com/rss",
        content_hash=f"hash-{title}",
        linked_entities=linked_entities,
        matched_terms=("ASELS", "TCMB"),
    )


class NewsContextTests(unittest.TestCase):
    def test_build_news_context_filters_by_decision_timestamp_and_lookback(self):
        items = (
            matched_item(
                "public by decision",
                "2026-09-24T09:00:00+00:00",
                ("ticker:ASELS", "macro:policy_rate"),
                url="https://example.com/public",
            ),
            matched_item(
                "future leak",
                "2026-09-25T09:00:00+00:00",
                ("ticker:ASELS",),
                url="https://example.com/future",
            ),
            matched_item(
                "outside lookback",
                "2026-09-10T09:00:00+00:00",
                ("ticker:ASELS",),
                url="https://example.com/old",
            ),
            matched_item(
                "missing timestamp",
                None,
                ("ticker:THYAO",),
                url="https://example.com/missing",
            ),
        )

        rows = build_news_context(
            items,
            decision_timestamp="2026-09-24T12:00:00+00:00",
            lookback_days=7,
        )
        by_entity = {f"{row.entity_type}:{row.entity_id}": row for row in rows}

        self.assertEqual(1, by_entity["ticker:ASELS"].news_count)
        self.assertEqual(("https://example.com/public",), by_entity["ticker:ASELS"].evidence_urls)
        self.assertEqual(0, by_entity["ticker:THYAO"].news_count)
        self.assertEqual(1, by_entity["macro:policy_rate"].news_count)

    def test_build_news_context_includes_all_fixed_universe_tickers(self):
        rows = build_news_context(
            (),
            decision_timestamp="2026-09-24T12:00:00+00:00",
            lookback_days=7,
        )
        ticker_rows = [row for row in rows if row.entity_type == "ticker"]

        self.assertEqual(30, len(ticker_rows))
        self.assertTrue(all(row.news_count == 0 for row in ticker_rows))

    def test_build_news_context_from_cache_writes_csv_and_report(self):
        items = (
            matched_item(
                "ASELS public news",
                "2026-09-24T09:00:00+00:00",
                ("ticker:ASELS", "sector:Technology / Defense"),
                source_id="source_a",
                url="https://example.com/a",
            ),
            matched_item(
                "ASELS second source",
                "2026-09-24T10:00:00+00:00",
                ("ticker:ASELS",),
                source_id="source_b",
                url="https://example.com/b",
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_path = tmp_path / "news_matched.jsonl"
            output_path = tmp_path / "news_context.csv"
            report_path = tmp_path / "context_sources.md"
            write_matched_news_jsonl(items, input_path)

            result = build_news_context_from_cache(
                input_path=input_path,
                output_path=output_path,
                report_path=report_path,
                decision_timestamp="2026-09-24T12:00:00+00:00",
                lookback_days=7,
            )

            with output_path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            asels = next(
                row for row in rows if row["entity_type"] == "ticker" and row["entity_id"] == "ASELS"
            )

            self.assertEqual(list(NEWS_CONTEXT_COLUMNS), list(rows[0].keys()))
            self.assertEqual("2", asels["news_count"])
            self.assertEqual("2", asels["source_count"])
            self.assertIn("https://example.com/a", asels["evidence_urls"])
            self.assertIn("# Context Sources Report", report_path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(result.rows), 31)


if __name__ == "__main__":
    unittest.main()
