"""Market cache coverage and quality audit helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data import load_universe, price_cache_path, read_price_cache
from src.settings import load_settings
from src.validation import BLOCKING, WARNING, validate_price_history


@dataclass(frozen=True)
class MarketCacheAuditRow:
    symbol: str
    role: str
    status: str
    row_count: int
    start_date: str | None
    end_date: str | None
    source: str | None
    download_timestamp: str | None
    warning_count: int
    blocking_count: int
    issues: tuple[str, ...]


@dataclass(frozen=True)
class MarketCacheAuditResult:
    rows: tuple[MarketCacheAuditRow, ...]
    output_path: Path

    @property
    def expected_count(self) -> int:
        return len(self.rows)

    @property
    def cached_count(self) -> int:
        return sum(1 for row in self.rows if row.row_count > 0)

    @property
    def pass_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "pass")

    @property
    def warning_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "warning")

    @property
    def error_count(self) -> int:
        return sum(1 for row in self.rows if row.status == "error")


def audit_market_cache_from_settings(
    output_path: str | Path | None = None,
) -> MarketCacheAuditResult:
    """Audit configured market cache and write the markdown report."""

    settings = load_settings()
    universe = load_universe(settings.paths.universe)
    symbols = [member.yahoo_symbol for member in universe]
    if settings.market_data.benchmark_symbol not in symbols:
        symbols.append(settings.market_data.benchmark_symbol)

    rows = audit_market_cache(
        symbols=symbols,
        benchmark_symbol=settings.market_data.benchmark_symbol,
        cache_dir=settings.paths.cache_dir,
        warn_on_small_sample_below=settings.validation.warn_on_small_sample_below,
    )
    path = write_market_cache_audit_report(
        rows=rows,
        output_path=output_path or settings.paths.reports_dir / "market_cache_audit.md",
        cache_dir=settings.paths.cache_dir,
        adjusted_price_policy=settings.market_data.adjusted_price_policy,
        configured_start_date=settings.market_data.start_date,
        configured_end_date=settings.market_data.end_date,
    )
    return MarketCacheAuditResult(rows=rows, output_path=path)


def audit_market_cache(
    symbols: list[str],
    benchmark_symbol: str,
    cache_dir: str | Path,
    warn_on_small_sample_below: int,
) -> tuple[MarketCacheAuditRow, ...]:
    """Audit cache coverage and validation status for expected symbols."""

    rows: list[MarketCacheAuditRow] = []
    for symbol in symbols:
        role = "benchmark" if symbol == benchmark_symbol else "universe"
        rows.append(
            _audit_symbol(
                symbol=symbol,
                role=role,
                cache_dir=Path(cache_dir),
                warn_on_small_sample_below=warn_on_small_sample_below,
            )
        )
    return tuple(rows)


def write_market_cache_audit_report(
    rows: tuple[MarketCacheAuditRow, ...] | list[MarketCacheAuditRow],
    output_path: str | Path,
    cache_dir: str | Path,
    adjusted_price_policy: str,
    configured_start_date: str,
    configured_end_date: str | None,
) -> Path:
    """Write market cache audit report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = tuple(rows)
    pass_count = sum(1 for row in rows if row.status == "pass")
    warning_count = sum(1 for row in rows if row.status == "warning")
    error_count = sum(1 for row in rows if row.status == "error")
    cached_count = sum(1 for row in rows if row.row_count > 0)
    lines = [
        "# Market Cache Audit",
        "",
        "Status: local market cache coverage and quality audit.",
        "",
        f"Cache directory: `{_display_path(Path(cache_dir))}`",
        f"Adjusted price policy: `{adjusted_price_policy}`",
        f"Configured start date: `{configured_start_date}`",
        f"Configured end date: `{configured_end_date or 'latest available'}`",
        "",
        "## Summary",
        "",
        f"Expected symbols: {len(rows)}",
        f"Cached symbols: {cached_count}",
        f"Pass: {pass_count}",
        f"Warning: {warning_count}",
        f"Error: {error_count}",
        "",
        "| Symbol | Role | Status | Rows | Start | End | Source | Download timestamp | Warnings | Blocking | Issues |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.symbol} | {row.role} | {row.status} | {row.row_count} | "
            f"{row.start_date or 'n/a'} | {row.end_date or 'n/a'} | "
            f"{row.source or 'n/a'} | {row.download_timestamp or 'n/a'} | "
            f"{row.warning_count} | {row.blocking_count} | "
            f"{_escape_table('; '.join(row.issues) if row.issues else 'none')} |"
        )
    lines.extend(
        [
            "",
            "Limitations:",
            "- Cache CSV files are local artifacts and are not committed.",
            "- This audit verifies local coverage and schema quality; it does not by itself create measured strategy results.",
            "- BIST 100 membership for the historical study period still needs to be documented separately if required by the instructor.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _audit_symbol(
    symbol: str,
    role: str,
    cache_dir: Path,
    warn_on_small_sample_below: int,
) -> MarketCacheAuditRow:
    cache_path = price_cache_path(cache_dir, symbol)
    if not cache_path.exists():
        return MarketCacheAuditRow(
            symbol=symbol,
            role=role,
            status="error",
            row_count=0,
            start_date=None,
            end_date=None,
            source=None,
            download_timestamp=None,
            warning_count=0,
            blocking_count=1,
            issues=("CACHE_FILE_MISSING",),
        )

    try:
        prices = read_price_cache(cache_dir, symbol)
        report = validate_price_history(prices, symbol, warn_on_small_sample_below)
    except Exception as exc:
        return MarketCacheAuditRow(
            symbol=symbol,
            role=role,
            status="error",
            row_count=0,
            start_date=None,
            end_date=None,
            source=None,
            download_timestamp=None,
            warning_count=0,
            blocking_count=1,
            issues=(str(exc),),
        )

    dates = pd.to_datetime(prices["date"], errors="coerce")
    warning_count = len(report.issues_by_severity(WARNING))
    blocking_count = len(report.issues_by_severity(BLOCKING))
    if blocking_count:
        status = "error"
    elif warning_count:
        status = "warning"
    else:
        status = "pass"
    return MarketCacheAuditRow(
        symbol=symbol,
        role=role,
        status=status,
        row_count=len(prices),
        start_date=dates.min().date().isoformat() if dates.notna().any() else None,
        end_date=dates.max().date().isoformat() if dates.notna().any() else None,
        source=_first_unique_value(prices, "source"),
        download_timestamp=_latest_timestamp(prices, "download_timestamp"),
        warning_count=warning_count,
        blocking_count=blocking_count,
        issues=tuple(issue.code for issue in report.issues),
    )


def _first_unique_value(frame: pd.DataFrame, column: str) -> str | None:
    if column not in frame.columns:
        return None
    values = [str(value) for value in frame[column].dropna().unique() if str(value).strip()]
    return values[0] if values else None


def _latest_timestamp(frame: pd.DataFrame, column: str) -> str | None:
    if column not in frame.columns:
        return None
    parsed = pd.to_datetime(frame[column], utc=True, errors="coerce")
    if parsed.dropna().empty:
        return None
    return parsed.max().isoformat()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
