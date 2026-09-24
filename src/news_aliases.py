"""Deterministic alias matching for RSS news context."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

from src.rss_news import (
    DEFAULT_NORMALIZED_RSS_OUTPUT_PATH,
    PROJECT_ROOT,
    RssNewsItem,
    load_news_jsonl,
)


DEFAULT_NEWS_ALIASES_PATH = PROJECT_ROOT / "config" / "news_aliases.csv"
DEFAULT_MATCHED_NEWS_OUTPUT_PATH = PROJECT_ROOT / "data" / "rss" / "news_matched.jsonl"
DEFAULT_ALIAS_MATCH_REPORT_PATH = PROJECT_ROOT / "reports" / "news_alias_matches.md"
ALLOWED_ENTITY_TYPES = ("ticker", "sector", "macro")
TURKISH_TRANSLATION = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "Ç": "c",
        "Ğ": "g",
        "İ": "i",
        "I": "i",
        "Ö": "o",
        "Ş": "s",
        "Ü": "u",
    }
)


@dataclass(frozen=True)
class NewsAlias:
    entity_type: str
    entity_id: str
    alias: str
    normalized_alias: str


@dataclass(frozen=True)
class AliasMatch:
    entity_type: str
    entity_id: str
    matched_term: str

    @property
    def linked_entity(self) -> str:
        return f"{self.entity_type}:{self.entity_id}"


@dataclass(frozen=True)
class MatchedNewsItem:
    source_id: str
    title: str
    url: str
    summary: str | None
    published_timestamp: str | None
    fetched_timestamp: str
    language: str
    category: str
    source_access: str
    raw_source_url: str
    content_hash: str
    linked_entities: tuple[str, ...]
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class AliasMatchSummary:
    total_items: int
    matched_items: int
    unmatched_items: int
    entity_counts: tuple[tuple[str, int], ...]


def load_news_aliases(path: str | Path = DEFAULT_NEWS_ALIASES_PATH) -> tuple[NewsAlias, ...]:
    """Load deterministic news aliases from CSV."""

    aliases: list[NewsAlias] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [
            column
            for column in ("entity_type", "entity_id", "alias")
            if column not in (reader.fieldnames or [])
        ]
        if missing:
            raise ValueError(f"missing alias columns: {', '.join(missing)}")

        for row_number, row in enumerate(reader, start=2):
            entity_type = _required_text(row, "entity_type", row_number).lower()
            if entity_type not in ALLOWED_ENTITY_TYPES:
                raise ValueError(
                    f"row {row_number}: entity_type must be one of "
                    f"{', '.join(ALLOWED_ENTITY_TYPES)}"
                )
            alias = _required_text(row, "alias", row_number)
            aliases.append(
                NewsAlias(
                    entity_type=entity_type,
                    entity_id=_required_text(row, "entity_id", row_number),
                    alias=alias,
                    normalized_alias=normalize_match_text(alias),
                )
            )
    return tuple(aliases)


def match_news_item(item: RssNewsItem, aliases: tuple[NewsAlias, ...]) -> MatchedNewsItem:
    """Attach deterministic alias matches to one RSS news item."""

    text = normalize_match_text(f"{item.title} {item.summary or ''}")
    matches: list[AliasMatch] = []
    seen: set[tuple[str, str, str]] = set()

    for alias in aliases:
        if _contains_alias(text, alias.normalized_alias):
            key = (alias.entity_type, alias.entity_id, alias.normalized_alias)
            if key in seen:
                continue
            seen.add(key)
            matches.append(
                AliasMatch(
                    entity_type=alias.entity_type,
                    entity_id=alias.entity_id,
                    matched_term=alias.alias,
                )
            )

    matches = sorted(matches, key=lambda match: (match.entity_type, match.entity_id, match.matched_term))
    linked_entities = tuple(dict.fromkeys(match.linked_entity for match in matches))
    matched_terms = tuple(match.matched_term for match in matches)
    return MatchedNewsItem(
        source_id=item.source_id,
        title=item.title,
        url=item.url,
        summary=item.summary,
        published_timestamp=item.published_timestamp,
        fetched_timestamp=item.fetched_timestamp,
        language=item.language,
        category=item.category,
        source_access=item.source_access,
        raw_source_url=item.raw_source_url,
        content_hash=item.content_hash,
        linked_entities=linked_entities,
        matched_terms=matched_terms,
    )


def match_news_items(
    items: tuple[RssNewsItem, ...] | list[RssNewsItem],
    aliases: tuple[NewsAlias, ...],
) -> tuple[MatchedNewsItem, ...]:
    """Attach alias matches to many RSS news items."""

    return tuple(match_news_item(item, aliases) for item in items)


def match_news_cache(
    input_path: str | Path = DEFAULT_NORMALIZED_RSS_OUTPUT_PATH,
    aliases_path: str | Path = DEFAULT_NEWS_ALIASES_PATH,
    output_path: str | Path = DEFAULT_MATCHED_NEWS_OUTPUT_PATH,
    report_path: str | Path = DEFAULT_ALIAS_MATCH_REPORT_PATH,
) -> tuple[MatchedNewsItem, ...]:
    """Load normalized RSS news, match aliases, and write output artifacts."""

    items = load_news_jsonl(input_path)
    aliases = load_news_aliases(aliases_path)
    matched = match_news_items(items, aliases)
    write_matched_news_jsonl(matched, output_path)
    write_alias_match_report(summarize_alias_matches(matched), report_path)
    return matched


def write_matched_news_jsonl(
    items: tuple[MatchedNewsItem, ...] | list[MatchedNewsItem],
    output_path: str | Path = DEFAULT_MATCHED_NEWS_OUTPUT_PATH,
) -> Path:
    """Write alias-enriched news records as JSONL."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(asdict(item), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    return path


def load_matched_news_jsonl(
    path: str | Path = DEFAULT_MATCHED_NEWS_OUTPUT_PATH,
) -> tuple[MatchedNewsItem, ...]:
    """Load alias-enriched news JSONL records from disk."""

    jsonl_path = Path(path)
    if not jsonl_path.exists():
        raise FileNotFoundError(f"matched news JSONL not found: {jsonl_path}")

    items: list[MatchedNewsItem] = []
    with jsonl_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                items.append(_matched_item_from_dict(row))
            except Exception as exc:
                raise ValueError(
                    f"invalid matched news JSONL row {line_number}: {exc}"
                ) from exc
    return tuple(items)



def summarize_alias_matches(
    items: tuple[MatchedNewsItem, ...] | list[MatchedNewsItem],
) -> AliasMatchSummary:
    """Summarize entity coverage for alias-enriched news."""

    counts: dict[str, int] = {}
    matched_items = 0
    for item in items:
        if item.linked_entities:
            matched_items += 1
        for entity in item.linked_entities:
            counts[entity] = counts.get(entity, 0) + 1
    return AliasMatchSummary(
        total_items=len(items),
        matched_items=matched_items,
        unmatched_items=len(items) - matched_items,
        entity_counts=tuple(sorted(counts.items())),
    )


def write_alias_match_report(
    summary: AliasMatchSummary,
    report_path: str | Path = DEFAULT_ALIAS_MATCH_REPORT_PATH,
) -> Path:
    """Write a small alias match coverage report."""

    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# News Alias Matches",
        "",
        f"Total items: {summary.total_items}",
        f"Matched items: {summary.matched_items}",
        f"Unmatched items: {summary.unmatched_items}",
        "",
        "| Entity | Item count |",
        "| --- | --- |",
    ]
    for entity, count in summary.entity_counts:
        lines.append(f"| {entity} | {count} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def normalize_match_text(value: str) -> str:
    """Normalize text for deterministic Turkish/English alias matching."""

    translated = value.translate(TURKISH_TRANSLATION)
    decomposed = unicodedata.normalize("NFKD", translated.casefold())
    without_marks = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    without_tags = re.sub(r"<[^>]+>", " ", without_marks)
    normalized = re.sub(r"[^a-z0-9]+", " ", without_tags)
    return re.sub(r"\s+", " ", normalized).strip()


def _contains_alias(text: str, alias: str) -> bool:
    if not alias:
        return False
    return re.search(rf"(^|\s){re.escape(alias)}($|\s)", text) is not None


def _required_text(row: dict[str, str], key: str, row_number: int) -> str:
    value = row.get(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"row {row_number}: missing {key}")
    return str(value).strip()


def _matched_item_from_dict(row: dict[str, object]) -> MatchedNewsItem:
    return MatchedNewsItem(
        source_id=_required_loaded_text(row, "source_id"),
        title=_required_loaded_text(row, "title"),
        url=_required_loaded_text(row, "url"),
        summary=_optional_loaded_text(row, "summary"),
        published_timestamp=_optional_loaded_text(row, "published_timestamp"),
        fetched_timestamp=_required_loaded_text(row, "fetched_timestamp"),
        language=_required_loaded_text(row, "language"),
        category=_required_loaded_text(row, "category"),
        source_access=_required_loaded_text(row, "source_access"),
        raw_source_url=_required_loaded_text(row, "raw_source_url"),
        content_hash=_required_loaded_text(row, "content_hash"),
        linked_entities=tuple(row.get("linked_entities") or ()),
        matched_terms=tuple(row.get("matched_terms") or ()),
    )


def _required_loaded_text(row: dict[str, object], key: str) -> str:
    value = row.get(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing {key}")
    return str(value).strip()


def _optional_loaded_text(row: dict[str, object], key: str) -> str | None:
    value = row.get(key)
    if value is None or str(value).strip() == "":
        return None
    return str(value).strip()
