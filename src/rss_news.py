"""RSS news source fetching and raw cache helpers."""

from __future__ import annotations

import hashlib
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Protocol

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RSS_SOURCES_PATH = PROJECT_ROOT / "config" / "rss_sources.yaml"
DEFAULT_RSS_OUTPUT_PATH = PROJECT_ROOT / "data" / "rss" / "news_raw.jsonl"
DEFAULT_NORMALIZED_RSS_OUTPUT_PATH = PROJECT_ROOT / "data" / "rss" / "news.jsonl"
DEFAULT_RSS_REPORT_PATH = PROJECT_ROOT / "reports" / "rss_fetch_status.md"
DEFAULT_RSS_SOURCE_HEALTH_PATH = PROJECT_ROOT / "reports" / "rss_source_health.md"


@dataclass(frozen=True)
class RssSource:
    source_id: str
    url: str
    language: str
    category: str
    enabled: bool = True


@dataclass(frozen=True)
class RssNewsItem:
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


@dataclass(frozen=True)
class RssSourceStatus:
    source_id: str
    status: str
    item_count: int
    detail: str


@dataclass(frozen=True)
class RssSourceHealth:
    source_id: str
    status: str
    raw_count: int
    normalized_count: int
    duplicate_count: int
    latest_published_timestamp: str | None
    detail: str


@dataclass(frozen=True)
class RssNormalizationResult:
    items: tuple[RssNewsItem, ...]
    source_health: tuple[RssSourceHealth, ...]
    output_path: Path
    report_path: Path


@dataclass(frozen=True)
class RssFetchResult:
    items: tuple[RssNewsItem, ...]
    statuses: tuple[RssSourceStatus, ...]
    output_path: Path
    report_path: Path

    @property
    def exit_code(self) -> int:
        return 0 if self.items else 1


class RssHttpClient(Protocol):
    def fetch(self, url: str) -> bytes:
        """Fetch a URL and return response bytes."""


class UrllibRssHttpClient:
    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch(self, url: str) -> bytes:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "agentic-bist-analytics/1.0"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read()


def load_rss_sources(path: str | Path = DEFAULT_RSS_SOURCES_PATH) -> tuple[RssSource, ...]:
    """Load enabled RSS source definitions from YAML."""

    with Path(path).open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    sources: list[RssSource] = []
    for index, row in enumerate(raw.get("sources", []), start=1):
        source_id = _required_text(row, "id", index)
        sources.append(
            RssSource(
                source_id=source_id,
                url=_required_text(row, "url", index),
                language=_required_text(row, "language", index),
                category=_required_text(row, "category", index),
                enabled=bool(row.get("enabled", True)),
            )
        )
    if not sources:
        raise ValueError("no RSS sources configured")
    return tuple(source for source in sources if source.enabled)


def fetch_rss_news(
    sources: tuple[RssSource, ...],
    output_path: str | Path = DEFAULT_RSS_OUTPUT_PATH,
    report_path: str | Path = DEFAULT_RSS_REPORT_PATH,
    client: RssHttpClient | None = None,
    fetched_timestamp: str | None = None,
) -> RssFetchResult:
    """Fetch RSS sources, cache normalized raw items, and write a source report."""

    active_client = client or UrllibRssHttpClient()
    timestamp = fetched_timestamp or datetime.now(UTC).isoformat()
    items: list[RssNewsItem] = []
    statuses: list[RssSourceStatus] = []

    for source in sources:
        try:
            body = active_client.fetch(source.url)
            source_items = parse_feed_items(body, source, timestamp)
        except Exception as exc:
            statuses.append(
                RssSourceStatus(
                    source_id=source.source_id,
                    status="error",
                    item_count=0,
                    detail=str(exc),
                )
            )
            continue

        items.extend(source_items)
        missing_timestamps = sum(1 for item in source_items if item.published_timestamp is None)
        if not source_items:
            status = "warning"
            detail = "feed returned no items"
        elif missing_timestamps:
            status = "warning"
            detail = f"{missing_timestamps} item(s) missing published_timestamp"
        else:
            status = "pass"
            detail = "fetched successfully"
        statuses.append(
            RssSourceStatus(
                source_id=source.source_id,
                status=status,
                item_count=len(source_items),
                detail=detail,
            )
        )

    output = write_news_jsonl(items, output_path)
    report = write_rss_fetch_report(statuses, report_path)
    return RssFetchResult(
        items=tuple(items),
        statuses=tuple(statuses),
        output_path=output,
        report_path=report,
    )


def parse_feed_items(
    body: bytes,
    source: RssSource,
    fetched_timestamp: str,
) -> tuple[RssNewsItem, ...]:
    """Parse RSS or Atom feed bytes into normalized raw news items."""

    root = ET.fromstring(_decode_feed_body(body))
    elements = list(root.findall("./channel/item"))
    if not elements:
        elements = list(root.findall(".//{http://www.w3.org/2005/Atom}entry"))

    items: list[RssNewsItem] = []
    for element in elements:
        title = _first_text(element, ("title", "{http://www.w3.org/2005/Atom}title"))
        url = _first_text(element, ("link", "guid"))
        atom_link = element.find("{http://www.w3.org/2005/Atom}link")
        if atom_link is not None and atom_link.attrib.get("href"):
            url = atom_link.attrib["href"].strip()
        if not title or not url:
            continue

        summary = _first_text(
            element,
            (
                "description",
                "summary",
                "{http://www.w3.org/2005/Atom}summary",
                "{http://www.w3.org/2005/Atom}content",
            ),
        )
        published = _first_text(
            element,
            (
                "pubDate",
                "published",
                "updated",
                "{http://www.w3.org/2005/Atom}published",
                "{http://www.w3.org/2005/Atom}updated",
            ),
        )
        published_timestamp = normalize_feed_timestamp(published)
        items.append(
            RssNewsItem(
                source_id=source.source_id,
                title=title,
                url=url,
                summary=summary,
                published_timestamp=published_timestamp,
                fetched_timestamp=fetched_timestamp,
                language=source.language,
                category=source.category,
                source_access="rss",
                raw_source_url=source.url,
                content_hash=_content_hash(
                    source.source_id,
                    title,
                    url,
                    published_timestamp or "",
                    summary or "",
                ),
            )
        )
    return tuple(items)


def normalize_feed_timestamp(value: str | None) -> str | None:
    """Normalize common RSS/Atom timestamps to UTC ISO format."""

    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except Exception:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat()


def write_news_jsonl(
    items: list[RssNewsItem] | tuple[RssNewsItem, ...],
    output_path: str | Path = DEFAULT_RSS_OUTPUT_PATH,
) -> Path:
    """Write raw RSS news records as JSONL."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(asdict(item), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    return path


def load_news_jsonl(path: str | Path) -> tuple[RssNewsItem, ...]:
    """Load RSS news JSONL records from disk."""

    jsonl_path = Path(path)
    if not jsonl_path.exists():
        raise FileNotFoundError(f"RSS JSONL not found: {jsonl_path}")

    items: list[RssNewsItem] = []
    with jsonl_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                items.append(_news_item_from_dict(row))
            except Exception as exc:
                raise ValueError(
                    f"invalid RSS JSONL row {line_number}: {exc}"
                ) from exc
    return tuple(items)


def normalize_rss_news_cache(
    raw_path: str | Path = DEFAULT_RSS_OUTPUT_PATH,
    output_path: str | Path = DEFAULT_NORMALIZED_RSS_OUTPUT_PATH,
    report_path: str | Path = DEFAULT_RSS_SOURCE_HEALTH_PATH,
    sources: tuple[RssSource, ...] | None = None,
    fetch_statuses: dict[str, RssSourceStatus] | None = None,
    as_of_timestamp: str | None = None,
    stale_after_hours: int = 24,
) -> RssNormalizationResult:
    """Normalize raw RSS JSONL, remove duplicates, and write source health."""

    raw_items = load_news_jsonl(raw_path)
    normalized_items = deduplicate_news_items(raw_items)
    source_health = build_source_health(
        raw_items=raw_items,
        normalized_items=normalized_items,
        sources=sources or (),
        fetch_statuses=fetch_statuses or {},
        as_of_timestamp=as_of_timestamp,
        stale_after_hours=stale_after_hours,
    )
    output = write_news_jsonl(normalized_items, output_path)
    report = write_source_health_report(source_health, report_path)
    return RssNormalizationResult(
        items=normalized_items,
        source_health=source_health,
        output_path=output,
        report_path=report,
    )


def deduplicate_news_items(
    items: tuple[RssNewsItem, ...] | list[RssNewsItem],
) -> tuple[RssNewsItem, ...]:
    """Return deterministic unique RSS items by URL, title, then content hash."""

    unique_by_url: set[str] = set()
    unique_by_title: set[str] = set()
    unique_by_hash: set[str] = set()
    deduped: list[RssNewsItem] = []

    for item in sorted(items, key=_dedup_sort_key):
        normalized_item = normalize_news_item(item)
        url_key = _normalize_url(normalized_item.url)
        title_key = _normalize_text(normalized_item.title).lower()
        hash_key = normalized_item.content_hash
        if url_key and url_key in unique_by_url:
            continue
        if title_key and title_key in unique_by_title:
            continue
        if hash_key in unique_by_hash:
            continue

        unique_by_url.add(url_key)
        unique_by_title.add(title_key)
        unique_by_hash.add(hash_key)
        deduped.append(normalized_item)

    return tuple(deduped)


def normalize_news_item(item: RssNewsItem) -> RssNewsItem:
    """Clean text fields and rebuild the content hash for normalized cache."""

    title = _normalize_text(item.title)
    summary = _normalize_text(item.summary) if item.summary else None
    url = item.url.strip()
    published = item.published_timestamp
    return RssNewsItem(
        source_id=item.source_id,
        title=title,
        url=url,
        summary=summary,
        published_timestamp=published,
        fetched_timestamp=item.fetched_timestamp,
        language=item.language,
        category=item.category,
        source_access=item.source_access,
        raw_source_url=item.raw_source_url.strip(),
        content_hash=_content_hash(
            item.source_id,
            title,
            _normalize_url(url),
            published or "",
            summary or "",
        ),
    )


def build_source_health(
    raw_items: tuple[RssNewsItem, ...] | list[RssNewsItem],
    normalized_items: tuple[RssNewsItem, ...] | list[RssNewsItem],
    sources: tuple[RssSource, ...] | list[RssSource],
    fetch_statuses: dict[str, RssSourceStatus] | None = None,
    as_of_timestamp: str | None = None,
    stale_after_hours: int = 24,
) -> tuple[RssSourceHealth, ...]:
    """Build source-level raw/normalized/dedup/stale health records."""

    fetch_statuses = fetch_statuses or {}
    as_of = _parse_iso_timestamp(as_of_timestamp) if as_of_timestamp else datetime.now(UTC)
    source_ids = sorted(
        {
            *(source.source_id for source in sources),
            *(item.source_id for item in raw_items),
            *(status.source_id for status in fetch_statuses.values()),
        }
    )
    health: list[RssSourceHealth] = []
    for source_id in source_ids:
        raw_for_source = [item for item in raw_items if item.source_id == source_id]
        normalized_for_source = [
            item for item in normalized_items if item.source_id == source_id
        ]
        latest = _latest_published_timestamp(raw_for_source)
        duplicate_count = max(len(raw_for_source) - len(normalized_for_source), 0)
        fetch_status = fetch_statuses.get(source_id)

        if fetch_status and fetch_status.status == "error":
            status = "error"
            detail = fetch_status.detail
        elif not raw_for_source:
            status = "warning"
            detail = "empty source output"
        elif latest is None:
            status = "warning"
            detail = "no published timestamps available"
        elif _hours_between(latest, as_of) > stale_after_hours:
            status = "warning"
            detail = f"latest item is older than {stale_after_hours} hours"
        elif duplicate_count:
            status = "pass"
            detail = f"deduplicated {duplicate_count} repeated item(s)"
        else:
            status = "pass"
            detail = "healthy"

        health.append(
            RssSourceHealth(
                source_id=source_id,
                status=status,
                raw_count=len(raw_for_source),
                normalized_count=len(normalized_for_source),
                duplicate_count=duplicate_count,
                latest_published_timestamp=latest,
                detail=detail,
            )
        )
    return tuple(health)


def write_source_health_report(
    source_health: tuple[RssSourceHealth, ...] | list[RssSourceHealth],
    report_path: str | Path = DEFAULT_RSS_SOURCE_HEALTH_PATH,
) -> Path:
    """Write source health report for normalized RSS cache."""

    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# RSS Source Health",
        "",
        "| Source | Status | Raw items | Normalized items | Duplicates | Latest published | Detail |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for health in source_health:
        lines.append(
            f"| {health.source_id} | {health.status} | {health.raw_count} | "
            f"{health.normalized_count} | {health.duplicate_count} | "
            f"{health.latest_published_timestamp or 'n/a'} | "
            f"{_escape_table(health.detail)} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def load_rss_fetch_status_report(
    report_path: str | Path = DEFAULT_RSS_REPORT_PATH,
) -> dict[str, RssSourceStatus]:
    """Load the markdown fetch status report written by P24."""

    path = Path(report_path)
    if not path.exists():
        return {}

    statuses: dict[str, RssSourceStatus] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or "Source" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        try:
            item_count = int(cells[2])
        except ValueError:
            item_count = 0
        statuses[cells[0]] = RssSourceStatus(
            source_id=cells[0],
            status=cells[1],
            item_count=item_count,
            detail=cells[3],
        )
    return statuses


def write_rss_fetch_report(
    statuses: list[RssSourceStatus] | tuple[RssSourceStatus, ...],
    report_path: str | Path = DEFAULT_RSS_REPORT_PATH,
) -> Path:
    """Write a compact source-level fetch report."""

    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# RSS Fetch Status",
        "",
        "| Source | Status | Items | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for status in statuses:
        lines.append(
            f"| {status.source_id} | {status.status} | {status.item_count} | "
            f"{_escape_table(status.detail)} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _first_text(element: ET.Element, names: tuple[str, ...]) -> str | None:
    for name in names:
        child = element.find(name)
        if child is not None:
            text = "".join(child.itertext()).strip()
            if text:
                return text
    return None


def _decode_feed_body(body: bytes) -> str | bytes:
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return body


def _content_hash(*parts: str) -> str:
    payload = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _news_item_from_dict(row: dict[str, object]) -> RssNewsItem:
    return RssNewsItem(
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


def _dedup_sort_key(item: RssNewsItem) -> tuple[str, str, str]:
    published = item.published_timestamp or item.fetched_timestamp
    return (published, item.source_id, item.url)


def _normalize_url(value: str) -> str:
    return value.strip().lower().rstrip("/")


def _normalize_text(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _latest_published_timestamp(items: list[RssNewsItem]) -> str | None:
    timestamps = [item.published_timestamp for item in items if item.published_timestamp]
    if not timestamps:
        return None
    return max(timestamps)


def _parse_iso_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _hours_between(start: str, end: datetime) -> float:
    return (end - _parse_iso_timestamp(start)).total_seconds() / 3600


def _required_text(row: dict[str, object], key: str, index: int) -> str:
    value = row.get(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"RSS source row {index} missing {key}")
    return str(value).strip()


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
