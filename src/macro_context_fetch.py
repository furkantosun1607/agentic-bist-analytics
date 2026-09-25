"""Generate local macro context records from yfinance FX and static curated rates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

import pandas as pd

from src.context import normalize_context
from src.macro_context_status import DEFAULT_MACRO_CONTEXT_INPUT_PATH
from src.settings import PROJECT_ROOT


DEFAULT_MACRO_FETCH_STATUS_PATH = PROJECT_ROOT / "reports" / "macro_context_fetch_status.md"
DEFAULT_FX_START_DATE = "2024-01-01"
DEFAULT_FX_PAIRS = (
    ("usd_try", "USDTRY=X", "TRY per USD"),
    ("eur_try", "EURTRY=X", "TRY per EUR"),
)

STATIC_MACRO_RECORDS = (
    {
        "context_id": "macro-tcmb-policy-rate-2026-09-10",
        "context_type": "macro",
        "scope": "macro",
        "indicator": "tcmb_policy_rate",
        "value": 37.0,
        "unit": "%",
        "observed_period_start": "2026-09-10",
        "observed_period_end": "2026-09-10",
        "publication_timestamp": "2026-09-10T14:00:00+03:00",
        "source": "tcmb_press_release",
        "source_url": "https://www.tcmb.gov.tr/wps/wcm/connect/EN/TCMB%2BEN/Main%2BMenu/Announcements/Press%2BReleases/2026/ANO2026-38",
        "source_access": "public",
        "notes": "CBRT kept the one-week repo auction rate at 37 percent.",
    },
    {
        "context_id": "macro-tuik-inflation-2026-08",
        "context_type": "macro",
        "scope": "macro",
        "indicator": "tuik_inflation",
        "value": 31.51,
        "unit": "% yoy",
        "observed_period_start": "2026-08-01",
        "observed_period_end": "2026-08-31",
        "publication_timestamp": "2026-09-03T10:00:00+03:00",
        "source": "tuik_cpi_release",
        "source_url": "https://veriportali.tuik.gov.tr/tr/press/58290/metadata",
        "source_access": "public",
        "notes": "August 2026 annual CPI inflation used as a static point-in-time macro record.",
    },
    {
        "context_id": "macro-fed-policy-rate-2026-09-16",
        "context_type": "macro",
        "scope": "global",
        "indicator": "fed_policy_rate",
        "value": 3.875,
        "unit": "% target midpoint",
        "observed_period_start": "2026-09-16",
        "observed_period_end": "2026-09-16",
        "publication_timestamp": "2026-09-16T14:00:00-04:00",
        "source": "federal_reserve_fomc_statement",
        "source_url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm",
        "source_access": "public",
        "notes": "Midpoint of the 3.75 to 4.00 percent federal funds target range.",
    },
)


@dataclass(frozen=True)
class MacroContextFetchError:
    source: str
    reason: str


@dataclass(frozen=True)
class MacroContextFetchResult:
    records: pd.DataFrame
    errors: tuple[MacroContextFetchError, ...]
    output_path: Path
    report_path: Path
    download_timestamp: str


class FxRateProvider(Protocol):
    def download(self, symbol: str, start: str, end: str | None) -> pd.DataFrame:
        """Download FX history for a Yahoo Finance symbol."""


class YFinanceFxRateProvider:
    """Yahoo Finance/yfinance FX provider."""

    def download(self, symbol: str, start: str, end: str | None) -> pd.DataFrame:
        import yfinance as yf

        cache_dir = PROJECT_ROOT / "data" / "yfinance_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(yf, "set_tz_cache_location"):
            yf.set_tz_cache_location(str(cache_dir))

        return yf.download(
            symbol,
            start=start,
            end=end,
            progress=False,
            auto_adjust=False,
            actions=False,
        )


def fetch_macro_context(
    output_path: str | Path = DEFAULT_MACRO_CONTEXT_INPUT_PATH,
    report_path: str | Path = DEFAULT_MACRO_FETCH_STATUS_PATH,
    provider: FxRateProvider | None = None,
    start_date: str = DEFAULT_FX_START_DATE,
    end_date: str | None = None,
    timezone: str = "Europe/Istanbul",
    download_timestamp: str | None = None,
) -> MacroContextFetchResult:
    """Generate macro context CSV from yfinance FX rows and static rate records."""

    active_provider = provider or YFinanceFxRateProvider()
    timestamp = download_timestamp or datetime.now(UTC).isoformat()
    rows: list[dict[str, object]] = []
    errors: list[MacroContextFetchError] = []

    for indicator, symbol, unit in DEFAULT_FX_PAIRS:
        try:
            raw = active_provider.download(symbol, start_date, end_date)
            rows.extend(
                build_fx_context_rows(
                    raw_rates=raw,
                    indicator=indicator,
                    symbol=symbol,
                    unit=unit,
                    download_timestamp=timestamp,
                    timezone=timezone,
                )
            )
        except Exception as exc:
            errors.append(MacroContextFetchError(source=symbol, reason=str(exc)))

    rows.extend(_static_macro_rows(timestamp))
    normalized = normalize_context(pd.DataFrame(rows))
    errors.extend(
        MacroContextFetchError(source="macro_context_import", reason=error.message)
        for error in normalized.errors
    )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized.records.to_csv(path, index=False)

    report = write_macro_context_fetch_report(
        MacroContextFetchResult(
            records=normalized.records,
            errors=tuple(errors),
            output_path=path,
            report_path=Path(report_path),
            download_timestamp=timestamp,
        )
    )
    return MacroContextFetchResult(
        records=normalized.records,
        errors=tuple(errors),
        output_path=path,
        report_path=report,
        download_timestamp=timestamp,
    )


def build_fx_context_rows(
    raw_rates: pd.DataFrame,
    indicator: str,
    symbol: str,
    unit: str,
    download_timestamp: str,
    timezone: str = "Europe/Istanbul",
) -> list[dict[str, object]]:
    """Convert yfinance FX prices into macro context rows."""

    if raw_rates is None or raw_rates.empty:
        raise ValueError("no FX rows returned")

    frame = raw_rates.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    if "Date" not in frame.columns:
        frame = frame.reset_index()
    frame = frame.rename(columns={"Date": "date", "Close": "close", "Adj Close": "adj_close"})
    if "date" not in frame.columns or "close" not in frame.columns:
        raise ValueError("missing FX date/close columns")

    frame = frame.dropna(subset=["date", "close"]).sort_values("date")
    download_time = pd.to_datetime(download_timestamp, utc=True, errors="raise")
    rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        observed_date = pd.to_datetime(row["date"], errors="raise").date()
        publication_timestamp = _next_morning_publication(observed_date, timezone)
        if pd.to_datetime(publication_timestamp, utc=True, errors="raise") > download_time:
            continue
        rows.append(
            {
                "context_id": f"macro-{indicator}-{observed_date.isoformat()}",
                "context_type": "macro",
                "scope": "macro",
                "indicator": indicator,
                "value": float(row["close"]),
                "unit": unit,
                "observed_period_start": observed_date.isoformat(),
                "observed_period_end": observed_date.isoformat(),
                "publication_timestamp": publication_timestamp,
                "download_timestamp": download_timestamp,
                "source": "yahoo_finance_fx",
                "source_url": f"https://finance.yahoo.com/quote/{symbol}",
                "source_access": "public",
                "notes": "Daily FX close from yfinance; made knowable from next local morning.",
            }
        )
    return rows


def write_macro_context_fetch_report(result: MacroContextFetchResult) -> Path:
    """Write macro context fetch/generation status report."""

    path = result.report_path
    path.parent.mkdir(parents=True, exist_ok=True)
    coverage = (
        result.records.groupby("indicator").size().sort_index().to_dict()
        if not result.records.empty
        else {}
    )
    lines = [
        "# Macro Context Fetch Status",
        "",
        "Status: `ready_with_rows`" if len(result.records) else "Status: `no_rows`",
        "",
        "Source mix: `yfinance_fx + static_curated_macro_records`",
        f"Rows written: {len(result.records)}",
        f"Output CSV: `{_display_path(result.output_path)}`",
        f"Download timestamp: `{result.download_timestamp}`",
        "",
        "Important limitation: TCMB/TUIK/FED static records are curated project inputs with explicit publication timestamps; they are not live API pulls.",
        "",
        "## Coverage",
        "",
        "| Indicator | Rows |",
        "| --- | ---: |",
    ]
    if coverage:
        for indicator, count in coverage.items():
            lines.append(f"| {indicator} | {count} |")
    else:
        lines.append("| n/a | 0 |")

    if result.errors:
        lines.extend(["", "## Errors", ""])
        for error in result.errors:
            lines.append(f"- `{error.source}`: {error.reason}")

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _static_macro_rows(download_timestamp: str) -> list[dict[str, object]]:
    rows = []
    for record in STATIC_MACRO_RECORDS:
        row = dict(record)
        row["download_timestamp"] = download_timestamp
        rows.append(row)
    return rows


def _next_morning_publication(observed_date, timezone: str) -> str:
    publication_date = observed_date + timedelta(days=1)
    return datetime.combine(
        publication_date,
        time(hour=9, minute=0),
        tzinfo=ZoneInfo(timezone),
    ).isoformat()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
