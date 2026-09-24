import json
import tempfile
import unittest
from pathlib import Path

from src.rss_news import (
    RssSource,
    fetch_rss_news,
    load_rss_sources,
    normalize_feed_timestamp,
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


if __name__ == "__main__":
    unittest.main()
