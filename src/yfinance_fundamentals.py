"""Yahoo Finance fundamentals adapter with conservative synthetic disclosure dates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

import pandas as pd

from src.data import UniverseMember
from src.fundamentals import normalize_fundamentals
from src.settings import PROJECT_ROOT


DEFAULT_SYNTHETIC_DISCLOSURE_LAG_DAYS = 40
DEFAULT_SYNTHETIC_DISCLOSURE_TIME = "18:30:00"
DEFAULT_FUNDAMENTALS_OUTPUT_PATH = PROJECT_ROOT / "data" / "fundamentals" / "fundamentals.csv"
DEFAULT_FETCH_STATUS_PATH = PROJECT_ROOT / "reports" / "fundamentals_fetch_status.md"

INCOME_ALIASES = {
    "revenue": ("Total Revenue", "Operating Revenue"),
    "gross_profit": ("Gross Profit",),
    "operating_profit": ("Operating Income", "Operating Income Or Loss"),
    "net_income": ("Net Income", "Net Income Common Stockholders"),
    "net_interest_income": ("Net Interest Income", "Interest Income"),
}
BALANCE_ALIASES = {
    "total_assets": ("Total Assets",),
    "total_liabilities": (
        "Total Liabilities Net Minority Interest",
        "Total Liabilities",
    ),
    "total_equity": (
        "Stockholders Equity",
        "Total Equity Gross Minority Interest",
        "Common Stock Equity",
    ),
    "total_debt": ("Total Debt", "Long Term Debt And Capital Lease Obligation"),
    "cash_and_equivalents": (
        "Cash And Cash Equivalents",
        "Cash Cash Equivalents And Short Term Investments",
    ),
}
CASHFLOW_ALIASES = {
    "operating_cash_flow": (
        "Operating Cash Flow",
        "Cash Flow From Continuing Operating Activities",
    ),
    "free_cash_flow": ("Free Cash Flow",),
}


@dataclass(frozen=True)
class YFinanceStatementBundle:
    income: pd.DataFrame
    balance_sheet: pd.DataFrame
    cashflow: pd.DataFrame


@dataclass(frozen=True)
class YFinanceFundamentalsError:
    symbol: str
    reason: str


@dataclass(frozen=True)
class YFinanceFundamentalsResult:
    records: pd.DataFrame
    errors: tuple[YFinanceFundamentalsError, ...]
    output_path: Path
    report_path: Path
    download_timestamp: str


class YFinanceFundamentalsProvider(Protocol):
    def fetch(self, symbol: str) -> YFinanceStatementBundle:
        """Fetch quarterly financial statements for a Yahoo Finance symbol."""


class LiveYFinanceFundamentalsProvider:
    """Live yfinance fundamentals provider."""

    def fetch(self, symbol: str) -> YFinanceStatementBundle:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        return YFinanceStatementBundle(
            income=ticker.quarterly_financials,
            balance_sheet=ticker.quarterly_balance_sheet,
            cashflow=ticker.quarterly_cashflow,
        )


def fetch_yfinance_fundamentals(
    universe: list[UniverseMember],
    output_path: str | Path = DEFAULT_FUNDAMENTALS_OUTPUT_PATH,
    report_path: str | Path = DEFAULT_FETCH_STATUS_PATH,
    provider: YFinanceFundamentalsProvider | None = None,
    synthetic_lag_days: int = DEFAULT_SYNTHETIC_DISCLOSURE_LAG_DAYS,
    synthetic_disclosure_time: str = DEFAULT_SYNTHETIC_DISCLOSURE_TIME,
    timezone: str = "Europe/Istanbul",
    download_timestamp: str | None = None,
) -> YFinanceFundamentalsResult:
    """Fetch yfinance quarterly statements and write project fundamentals CSV."""

    active_provider = provider or LiveYFinanceFundamentalsProvider()
    timestamp = download_timestamp or datetime.now(UTC).isoformat()
    rows: list[dict[str, object]] = []
    errors: list[YFinanceFundamentalsError] = []

    for member in universe:
        try:
            bundle = active_provider.fetch(member.yahoo_symbol)
            member_rows = build_yfinance_fundamentals_rows(
                member=member,
                bundle=bundle,
                download_timestamp=timestamp,
                synthetic_lag_days=synthetic_lag_days,
                synthetic_disclosure_time=synthetic_disclosure_time,
                timezone=timezone,
            )
        except Exception as exc:
            errors.append(YFinanceFundamentalsError(symbol=member.yahoo_symbol, reason=str(exc)))
            continue

        if not member_rows:
            errors.append(
                YFinanceFundamentalsError(
                    symbol=member.yahoo_symbol,
                    reason="no mappable quarterly fundamentals rows returned",
                )
            )
            continue
        rows.extend(member_rows)

    normalized = normalize_fundamentals(pd.DataFrame(rows), universe)
    errors.extend(
        YFinanceFundamentalsError(symbol="import", reason=error.message)
        for error in normalized.errors
    )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized.records.to_csv(path, index=False)

    status_path = write_yfinance_fundamentals_fetch_report(
        YFinanceFundamentalsResult(
            records=normalized.records,
            errors=tuple(errors),
            output_path=path,
            report_path=Path(report_path),
            download_timestamp=timestamp,
        ),
        synthetic_lag_days=synthetic_lag_days,
        synthetic_disclosure_time=synthetic_disclosure_time,
        timezone=timezone,
    )
    return YFinanceFundamentalsResult(
        records=normalized.records,
        errors=tuple(errors),
        output_path=path,
        report_path=status_path,
        download_timestamp=timestamp,
    )


def build_yfinance_fundamentals_rows(
    member: UniverseMember,
    bundle: YFinanceStatementBundle,
    download_timestamp: str,
    synthetic_lag_days: int = DEFAULT_SYNTHETIC_DISCLOSURE_LAG_DAYS,
    synthetic_disclosure_time: str = DEFAULT_SYNTHETIC_DISCLOSURE_TIME,
    timezone: str = "Europe/Istanbul",
) -> list[dict[str, object]]:
    """Convert one symbol's yfinance statements into raw fundamentals rows."""

    income = _statement_lookup(bundle.income)
    balance = _statement_lookup(bundle.balance_sheet)
    cashflow = _statement_lookup(bundle.cashflow)
    periods = sorted(set(income) | set(balance) | set(cashflow))
    rows: list[dict[str, object]] = []

    for period_end in periods:
        row = {
            "ticker": member.ticker,
            "period_end": period_end,
            "period_type": "quarterly",
            "disclosure_timestamp": synthetic_disclosure_timestamp(
                period_end,
                lag_days=synthetic_lag_days,
                disclosure_time=synthetic_disclosure_time,
                timezone=timezone,
            ),
            "download_timestamp": download_timestamp,
            "source": f"yahoo_finance_synthetic_disclosure_{synthetic_lag_days}d",
            "currency": "TRY",
        }
        _add_metrics(row, income.get(period_end, {}), INCOME_ALIASES)
        _add_metrics(row, balance.get(period_end, {}), BALANCE_ALIASES)
        _add_metrics(row, cashflow.get(period_end, {}), CASHFLOW_ALIASES)
        if any(value is not None for key, value in row.items() if key not in _METADATA_KEYS):
            rows.append(row)

    return rows


def synthetic_disclosure_timestamp(
    period_end: str,
    lag_days: int = DEFAULT_SYNTHETIC_DISCLOSURE_LAG_DAYS,
    disclosure_time: str = DEFAULT_SYNTHETIC_DISCLOSURE_TIME,
    timezone: str = "Europe/Istanbul",
) -> str:
    """Return a conservative synthetic disclosure timestamp for a period end."""

    period_date = pd.to_datetime(period_end, errors="raise").date()
    hour, minute, second = (int(part) for part in disclosure_time.split(":"))
    disclosure_date = period_date + timedelta(days=lag_days)
    return datetime.combine(
        disclosure_date,
        time(hour=hour, minute=minute, second=second),
        tzinfo=ZoneInfo(timezone),
    ).isoformat()


def write_yfinance_fundamentals_fetch_report(
    result: YFinanceFundamentalsResult,
    synthetic_lag_days: int,
    synthetic_disclosure_time: str,
    timezone: str,
) -> Path:
    """Write a compact fetch status report for yfinance fundamentals."""

    path = result.report_path
    path.parent.mkdir(parents=True, exist_ok=True)
    coverage = (
        result.records.groupby("ticker").size().sort_index().to_dict()
        if not result.records.empty
        else {}
    )
    lines = [
        "# Fundamentals Fetch Status",
        "",
        "Status: `ready_with_rows`" if len(result.records) else "Status: `no_rows`",
        "",
        f"Source: `yahoo_finance`",
        f"Synthetic disclosure rule: `period_end + {synthetic_lag_days} days at {synthetic_disclosure_time} {timezone}`",
        f"Rows written: {len(result.records)}",
        f"Output CSV: `{_display_path(result.output_path)}`",
        f"Download timestamp: `{result.download_timestamp}`",
        "",
        "Important limitation: synthetic disclosure timestamps are conservative project assumptions, not exact KAP publication times.",
        "",
        "## Coverage",
        "",
        "| Ticker | Rows |",
        "| --- | ---: |",
    ]
    if coverage:
        for ticker, count in coverage.items():
            lines.append(f"| {ticker} | {count} |")
    else:
        lines.append("| n/a | 0 |")

    if result.errors:
        lines.extend(["", "## Errors", ""])
        for error in result.errors:
            lines.append(f"- `{error.symbol}`: {error.reason}")

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


_METADATA_KEYS = {
    "ticker",
    "period_end",
    "period_type",
    "disclosure_timestamp",
    "download_timestamp",
    "source",
    "currency",
}


def _statement_lookup(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    if frame is None or frame.empty:
        return {}

    normalized = frame.copy()
    if "index" in normalized.columns:
        normalized = normalized.set_index("index")

    lookup: dict[str, dict[str, object]] = {}
    for column in normalized.columns:
        period_end = pd.to_datetime(column, errors="coerce")
        if pd.isna(period_end):
            continue
        period_key = period_end.date().isoformat()
        values: dict[str, object] = {}
        for raw_label, value in normalized[column].items():
            if pd.isna(value):
                continue
            values[_normalize_label(str(raw_label))] = value
        lookup[period_key] = values
    return lookup


def _add_metrics(
    row: dict[str, object],
    values: dict[str, object],
    aliases: dict[str, tuple[str, ...]],
) -> None:
    for output_column, names in aliases.items():
        row[output_column] = _first_metric(values, names)


def _first_metric(values: dict[str, object], names: tuple[str, ...]) -> float | None:
    for name in names:
        value = values.get(_normalize_label(name))
        if value is not None:
            return float(value)
    return None


def _normalize_label(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").split())


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
