import json
import tempfile
import unittest
from pathlib import Path

from src.rss_news import (
    RssSource,
    RssSourceStatus,
    build_source_health,
    deduplicate_news_items,
    fetch_rss_news,
    load_rss_sources,
    normalize_feed_timestamp,
    normalize_news_item,
    normalize_rss_news_cache,
    parse_feed_items,
)


RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Economy</title>
    <item>
      <title>TCMB faiz kararini acikladi</title>
      <link>https://example.com/news/1</link>
      <description>Politika faizi haberi.</description>
      <pubDate>Thu, 24 Sep 2026 09:30:00 +0300</pubDate>
    </item>
    <item>
      <title>ASELS yeni sozlesme duyurdu</title>
      <link>https://example.com/news/2</link>
      <description>Sirket haberi.</description>
    </item>
  </channel>
</rss>
"""


class FakeClient:
    def __init__(self, responses):
        self.responses = responses

    def fetch(self, url):
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response


class RssNewsTests(unittest.TestCase):
    def test_load_rss_sources_from_config(self):
        sources = load_rss_sources()

        self.assertGreaterEqual(len(sources), 8)
        self.assertIn("ntv_ekonomi", {source.source_id for source in sources})

    def test_parse_feed_items_normalizes_required_fields(self):
        source = RssSource(
            source_id="example",
            url="https://example.com/rss",
            language="tr",
            category="economy",
        )

        items = parse_feed_items(
            RSS_BODY,
            source,
            fetched_timestamp="2026-09-24T09:45:00+00:00",
        )

        self.assertEqual(2, len(items))
        self.assertEqual("example", items[0].source_id)
        self.assertEqual("rss", items[0].source_access)
        self.assertEqual("2026-09-24T06:30:00+00:00", items[0].published_timestamp)
        self.assertIsNone(items[1].published_timestamp)
        self.assertEqual(64, len(items[0].content_hash))

    def test_fetch_continues_when_one_source_fails_and_writes_report(self):
        sources = (
            RssSource("ok_source", "https://example.com/rss", "tr", "economy"),
            RssSource("bad_source", "https://example.com/bad", "tr", "economy"),
        )
        client = FakeClient(
            {
                "https://example.com/rss": RSS_BODY,
                "https://example.com/bad": RuntimeError("network down"),
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            result = fetch_rss_news(
                sources=sources,
                output_path=tmp_path / "news_raw.jsonl",
                report_path=tmp_path / "rss_fetch_status.md",
                client=client,
                fetched_timestamp="2026-09-24T10:00:00+00:00",
            )

            self.assertEqual(0, result.exit_code)
            self.assertEqual(2, len(result.items))
            self.assertEqual(["warning", "error"], [status.status for status in result.statuses])

            rows = [
                json.loads(line)
                for line in result.output_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual("ok_source", rows[0]["source_id"])
            self.assertIn("bad_source", result.report_path.read_text(encoding="utf-8"))

    def test_normalize_feed_timestamp_returns_none_for_invalid_values(self):
        self.assertIsNone(normalize_feed_timestamp(None))
        self.assertIsNone(normalize_feed_timestamp("not a timestamp"))

    def test_deduplicate_news_items_uses_url_title_and_hash_keys(self):
        source = RssSource("example", "https://example.com/rss", "tr", "economy")
        items = list(
            parse_feed_items(
                RSS_BODY,
                source,
                fetched_timestamp="2026-09-24T10:00:00+00:00",
            )
        )
        duplicate_url = items[0]
        duplicate_title = type(items[1])(
            source_id="other",
            title=items[1].title.upper(),
            url="https://example.com/other-url",
            summary=items[1].summary,
            published_timestamp=items[1].published_timestamp,
            fetched_timestamp=items[1].fetched_timestamp,
            language=items[1].language,
            category=items[1].category,
            source_access=items[1].source_access,
            raw_source_url=items[1].raw_source_url,
            content_hash="different-hash",
        )

        deduped = deduplicate_news_items([*items, duplicate_url, duplicate_title])

        self.assertEqual(2, len(deduped))

    def test_normalize_news_item_strips_html_from_text_fields(self):
        source = RssSource("example", "https://example.com/rss", "tr", "economy")
        item = parse_feed_items(
            RSS_BODY.replace(
                b"Politika faizi haberi.",
                b"<p>Politika&#160;faizi <strong>haberi</strong>.</p>",
            ),
            source,
            fetched_timestamp="2026-09-24T10:00:00+00:00",
        )[0]

        normalized = normalize_news_item(item)

        self.assertEqual("Politika faizi haberi.", normalized.summary)
        self.assertNotEqual(item.content_hash, normalized.content_hash)

    def test_build_source_health_reports_duplicate_error_empty_and_stale_sources(self):
        source = RssSource("example", "https://example.com/rss", "tr", "economy")
        items = parse_feed_items(
            RSS_BODY,
            source,
            fetched_timestamp="2026-09-24T10:00:00+00:00",
        )
        raw_items = (*items, items[0])
        normalized = deduplicate_news_items(raw_items)

        health = build_source_health(
            raw_items=raw_items,
            normalized_items=normalized,
            sources=(
                source,
                RssSource("empty", "https://example.com/empty", "tr", "economy"),
                RssSource("failed", "https://example.com/fail", "tr", "economy"),
            ),
            fetch_statuses={
                "failed": RssSourceStatus("failed", "error", 0, "network down")
            },
            as_of_timestamp="2026-09-26T10:00:00+00:00",
            stale_after_hours=24,
        )
        by_source = {record.source_id: record for record in health}

        self.assertEqual("warning", by_source["example"].status)
        self.assertEqual(1, by_source["example"].duplicate_count)
        self.assertIn("older than 24 hours", by_source["example"].detail)
        self.assertEqual("warning", by_source["empty"].status)
        self.assertEqual("error", by_source["failed"].status)

    def test_normalize_rss_news_cache_writes_jsonl_and_source_health_report(self):
        source = RssSource("example", "https://example.com/rss", "tr", "economy")
        items = parse_feed_items(
            RSS_BODY,
            source,
            fetched_timestamp="2026-09-24T10:00:00+00:00",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_path = tmp_path / "news_raw.jsonl"
            output_path = tmp_path / "news.jsonl"
            report_path = tmp_path / "rss_source_health.md"
            raw_path.write_text(
                "\n".join(json.dumps(item.__dict__) for item in (*items, items[0])),
                encoding="utf-8",
            )

            result = normalize_rss_news_cache(
                raw_path=raw_path,
                output_path=output_path,
                report_path=report_path,
                sources=(source,),
                as_of_timestamp="2026-09-24T12:00:00+00:00",
            )

            self.assertEqual(2, len(result.items))
            self.assertNotIn("<", result.items[0].summary or "")
            self.assertTrue(output_path.exists())
            self.assertIn("# RSS Source Health", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
