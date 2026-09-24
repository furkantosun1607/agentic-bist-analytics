"""Decision-time safe RSS news context summaries."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.data import DEFAULT_UNIVERSE_PATH, load_universe
from src.news_aliases import (
    DEFAULT_MATCHED_NEWS_OUTPUT_PATH,
    MatchedNewsItem,
    load_matched_news_jsonl,
)
from src.rss_news import PROJECT_ROOT


DEFAULT_NEWS_CONTEXT_OUTPUT_PATH = PROJECT_ROOT / "data" / "rss" / "news_context.csv"
DEFAULT_CONTEXT_REPORT_PATH = PROJECT_ROOT / "reports" / "context_sources.md"
NEWS_CONTEXT_COLUMNS = (
    "entity_type",
    "entity_id",
    "decision_timestamp",
    "lookback_days",
    "news_count",
    "source_count",
    "latest_news_timestamp",
    "evidence_urls",
    "matched_terms",
)


@dataclass(frozen=True)
class NewsContextRow:
    entity_type: str
    entity_id: str
    decision_timestamp: str
    lookback_days: int
    news_count: int
    source_count: int
    latest_news_timestamp: str | None
    evidence_urls: tuple[str, ...]
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class NewsContextResult:
    rows: tuple[NewsContextRow, ...]
    output_path: Path
    report_path: Path


def build_news_context(
    items: tuple[MatchedNewsItem, ...] | list[MatchedNewsItem],
    decision_timestamp: str,
    lookback_days: int = 7,
    universe_path: str | Path = DEFAULT_UNIVERSE_PATH,
) -> tuple[NewsContextRow, ...]:
    """Build entity-level news context using only public-by-decision items."""

    if lookback_days < 0:
        raise ValueError("lookback_days must be non-negative")

    decision_time = _parse_timestamp(decision_timestamp)
    start_time = decision_time - timedelta(days=lookback_days)
    public_items = [
        item
        for item in items
        if item.published_timestamp
        and start_time <= _parse_timestamp(item.published_timestamp) <= decision_time
    ]

    entity_items: dict[str, list[MatchedNewsItem]] = {}
    for item in public_items:
        for entity in item.linked_entities:
            entity_items.setdefault(entity, []).append(item)

    required_entities = _required_ticker_entities(universe_path)
    required_entities.update(entity_items)
    rows = [
        _build_context_row(entity, entity_items.get(entity, []), decision_timestamp, lookback_days)
        for entity in sorted(required_entities)
    ]
    return tuple(rows)


def build_news_context_from_cache(
    input_path: str | Path = DEFAULT_MATCHED_NEWS_OUTPUT_PATH,
    output_path: str | Path = DEFAULT_NEWS_CONTEXT_OUTPUT_PATH,
    report_path: str | Path = DEFAULT_CONTEXT_REPORT_PATH,
    decision_timestamp: str | None = None,
    lookback_days: int = 7,
    universe_path: str | Path = DEFAULT_UNIVERSE_PATH,
) -> NewsContextResult:
    """Load matched RSS cache, build context rows, and write artifacts."""

    decision = decision_timestamp or datetime.now(UTC).isoformat()
    rows = build_news_context(
        load_matched_news_jsonl(input_path),
        decision_timestamp=decision,
        lookback_days=lookback_days,
        universe_path=universe_path,
    )
    output = write_news_context_csv(rows, output_path)
    report = write_context_sources_report(rows, report_path)
    return NewsContextResult(rows=rows, output_path=output, report_path=report)


def write_news_context_csv(
    rows: tuple[NewsContextRow, ...] | list[NewsContextRow],
    output_path: str | Path = DEFAULT_NEWS_CONTEXT_OUTPUT_PATH,
) -> Path:
    """Write news context rows to CSV."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(NEWS_CONTEXT_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "entity_type": row.entity_type,
                    "entity_id": row.entity_id,
                    "decision_timestamp": row.decision_timestamp,
                    "lookback_days": row.lookback_days,
                    "news_count": row.news_count,
                    "source_count": row.source_count,
                    "latest_news_timestamp": row.latest_news_timestamp or "",
                    "evidence_urls": ";".join(row.evidence_urls),
                    "matched_terms": ";".join(row.matched_terms),
                }
            )
    return path


def write_context_sources_report(
    rows: tuple[NewsContextRow, ...] | list[NewsContextRow],
    report_path: str | Path = DEFAULT_CONTEXT_REPORT_PATH,
) -> Path:
    """Write the context sources report with RSS news context status."""

    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    total_rows = len(rows)
    active_rows = [row for row in rows if row.news_count > 0]
    ticker_rows = [row for row in rows if row.entity_type == "ticker"]
    active_tickers = [row for row in ticker_rows if row.news_count > 0]
    lines = [
        "# Context Sources Report",
        "",
        "Status: RSS news context pipeline is implemented for cached, timestamped, legally accessible RSS records. Macro and video context schemas remain available; video is not required for the current RSS-only flow.",
        "",
        "Context types:",
        "- Macro: USD/TRY, EUR/TRY, TCMB policy rate, TUIK inflation and Fed policy-rate records.",
        "- News: RSS company, sector and macro event records with publication and fetch timestamps.",
        "- Video: optional instructor-approved public-video segments with timestamps and verified claims.",
        "",
        "## RSS News Context",
        "",
        f"Context rows: {total_rows}",
        f"Ticker rows: {len(ticker_rows)}",
        f"Tickers with RSS context: {len(active_tickers)}",
        f"Entities with RSS context: {len(active_rows)}",
        "",
        "| Entity | News count | Sources | Latest published | Evidence URLs |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in sorted(active_rows, key=lambda item: (-item.news_count, item.entity_type, item.entity_id))[:20]:
        evidence = "<br>".join(row.evidence_urls[:3])
        lines.append(
            f"| {row.entity_type}:{row.entity_id} | {row.news_count} | "
            f"{row.source_count} | {row.latest_news_timestamp or 'n/a'} | {evidence} |"
        )
    if not active_rows:
        lines.append("| n/a | 0 | 0 | n/a | n/a |")
    lines.extend(
        [
            "",
            "Decision-time rule:",
            "- Only RSS records with `published_timestamp <= decision_timestamp` are included.",
            "- The default lookback window is 7 days.",
            "- Alias matches are context evidence, not trade signals.",
            "",
            "Limitations:",
            "- RSS source availability and publication timestamps can vary by publisher.",
            "- Source access and licensing must be respected before records are used in final conclusions.",
            "- This report is historical research infrastructure, not investment advice.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _build_context_row(
    entity: str,
    items: list[MatchedNewsItem],
    decision_timestamp: str,
    lookback_days: int,
) -> NewsContextRow:
    entity_type, entity_id = entity.split(":", maxsplit=1)
    sources = sorted({item.source_id for item in items})
    timestamps = [item.published_timestamp for item in items if item.published_timestamp]
    evidence_urls = tuple(dict.fromkeys(item.url for item in items))
    matched_terms = tuple(
        sorted({term for item in items for term in item.matched_terms})
    )
    return NewsContextRow(
        entity_type=entity_type,
        entity_id=entity_id,
        decision_timestamp=decision_timestamp,
        lookback_days=lookback_days,
        news_count=len(items),
        source_count=len(sources),
        latest_news_timestamp=max(timestamps) if timestamps else None,
        evidence_urls=evidence_urls,
        matched_terms=matched_terms,
    )


def _required_ticker_entities(universe_path: str | Path) -> set[str]:
    return {f"ticker:{member.ticker}" for member in load_universe(universe_path)}


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
