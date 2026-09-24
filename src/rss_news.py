"""RSS news source fetching and raw cache helpers."""

from __future__ import annotations

import hashlib
import json
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
DEFAULT_RSS_REPORT_PATH = PROJECT_ROOT / "reports" / "rss_fetch_status.md"


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
        if child is not None and child.text and child.text.strip():
            return child.text.strip()
    return None


def _decode_feed_body(body: bytes) -> str | bytes:
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return body


def _content_hash(*parts: str) -> str:
    payload = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _required_text(row: dict[str, object], key: str, index: int) -> str:
    value = row.get(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"RSS source row {index} missing {key}")
    return str(value).strip()


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
