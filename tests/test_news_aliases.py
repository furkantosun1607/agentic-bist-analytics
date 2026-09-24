import json
import tempfile
import unittest
from pathlib import Path

from src.news_aliases import (
    load_news_aliases,
    match_news_cache,
    match_news_item,
    normalize_match_text,
    summarize_alias_matches,
)
from src.rss_news import RssNewsItem, write_news_jsonl


def news_item(title: str, summary: str | None = None) -> RssNewsItem:
    return RssNewsItem(
        source_id="test_source",
        title=title,
        url=f"https://example.com/{abs(hash(title))}",
        summary=summary,
        published_timestamp="2026-09-24T10:00:00+00:00",
        fetched_timestamp="2026-09-24T10:05:00+00:00",
        language="tr",
        category="economy",
        source_access="rss",
        raw_source_url="https://example.com/rss",
        content_hash=f"hash-{abs(hash(title))}",
    )


class NewsAliasesTests(unittest.TestCase):
    def test_load_news_aliases_from_config(self):
        aliases = load_news_aliases()

        self.assertGreaterEqual(len(aliases), 100)
        self.assertIn("ASELS", {alias.entity_id for alias in aliases})
        self.assertIn("policy_rate", {alias.entity_id for alias in aliases})

    def test_normalize_match_text_handles_turkish_characters(self):
        self.assertEqual(
            "turk hava yollari doviz",
            normalize_match_text("Türk Hava Yolları döviz"),
        )

    def test_match_news_item_links_ticker_sector_and_macro_entities(self):
        aliases = load_news_aliases()
        item = news_item(
            "Türk Hava Yolları ve havacılık hisseleri",
            "TCMB faiz kararı ve döviz kuru piyasada izleniyor.",
        )

        matched = match_news_item(item, aliases)

        self.assertIn("ticker:THYAO", matched.linked_entities)
        self.assertIn("sector:Transportation / Airlines", matched.linked_entities)
        self.assertIn("macro:policy_rate", matched.linked_entities)
        self.assertIn("macro:fx", matched.linked_entities)
        self.assertIn("Turk Hava Yollari", matched.matched_terms)

    def test_unmatched_news_item_is_kept_without_trade_signal(self):
        aliases = load_news_aliases()
        item = news_item("Kultur sanat etkinligi aciklandi", "Genel gundem haberi.")

        matched = match_news_item(item, aliases)

        self.assertEqual((), matched.linked_entities)
        self.assertEqual((), matched.matched_terms)

    def test_match_news_cache_writes_linked_entities_and_report(self):
        items = (
            news_item("ASELSAN yeni savunma sozlesmesi acikladi"),
            news_item("Kuresel tahvil faizi ve Fed piyasalari etkiledi"),
            news_item("Gundem disi haber"),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_path = tmp_path / "news.jsonl"
            output_path = tmp_path / "news_matched.jsonl"
            report_path = tmp_path / "news_alias_matches.md"
            write_news_jsonl(items, input_path)

            matched = match_news_cache(
                input_path=input_path,
                aliases_path="config/news_aliases.csv",
                output_path=output_path,
                report_path=report_path,
            )

            rows = [
                json.loads(line)
                for line in output_path.read_text(encoding="utf-8").splitlines()
            ]
            summary = summarize_alias_matches(matched)

            self.assertEqual(3, len(rows))
            self.assertIn("ticker:ASELS", rows[0]["linked_entities"])
            self.assertIn("macro:global_rates", rows[1]["linked_entities"])
            self.assertEqual(2, summary.matched_items)
            self.assertIn("# News Alias Matches", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
