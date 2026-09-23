"""Point-in-time quarterly fundamentals schema and import helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.data import UniverseMember
from src.validation import PointInTimeRecord


FUNDAMENTALS_COLUMNS = (
    "ticker",
    "yahoo_symbol",
    "sector",
    "metric_profile",
    "period_end",
    "period_type",
    "disclosure_timestamp",
    "download_timestamp",
    "source",
    "currency",
    "revenue",
    "gross_profit",
    "operating_profit",
    "net_income",
    "net_interest_income",
    "total_assets",
    "total_liabilities",
    "total_equity",
    "total_debt",
    "cash_and_equivalents",
    "operating_cash_flow",
    "free_cash_flow",
)
REQUIRED_FUNDAMENTALS_COLUMNS = (
    "ticker",
    "period_end",
    "period_type",
    "disclosure_timestamp",
    "download_timestamp",
    "source",
)
NUMERIC_FUNDAMENTALS_COLUMNS = (
    "revenue",
    "gross_profit",
    "operating_profit",
    "net_income",
    "net_interest_income",
    "total_assets",
    "total_liabilities",
    "total_equity",
    "total_debt",
    "cash_and_equivalents",
    "operating_cash_flow",
    "free_cash_flow",
)
ALLOWED_PERIOD_TYPES = ("quarterly", "annual")
BANKING_SECTOR_LABELS = ("bank", "banking")


@dataclass(frozen=True)
class FundamentalsImportError:
    row_number: int | None
    message: str


@dataclass(frozen=True)
class FundamentalsImportResult:
    records: pd.DataFrame
    errors: tuple[FundamentalsImportError, ...]


class FundamentalsSchemaError(ValueError):
    """Raised when fundamentals input cannot be normalized."""


def load_fundamentals_csv(
    path: str | Path,
    universe: Iterable[UniverseMember],
) -> FundamentalsImportResult:
    """Load fundamentals from CSV into the normalized point-in-time schema."""

    try:
        raw = pd.read_csv(path)
    except Exception as exc:
        return FundamentalsImportResult(
            records=empty_fundamentals_frame(),
            errors=(FundamentalsImportError(row_number=None, message=str(exc)),),
        )

    return normalize_fundamentals(raw, universe)


def normalize_fundamentals(
    raw: pd.DataFrame,
    universe: Iterable[UniverseMember],
) -> FundamentalsImportResult:
    """Normalize raw fundamentals records and collect row-level errors."""

    errors: list[FundamentalsImportError] = []
    if raw is None or raw.empty:
        return FundamentalsImportResult(
            records=empty_fundamentals_frame(),
            errors=(FundamentalsImportError(row_number=None, message="no fundamentals rows"),),
        )

    missing_columns = [column for column in REQUIRED_FUNDAMENTALS_COLUMNS if column not in raw.columns]
    if missing_columns:
        return FundamentalsImportResult(
            records=empty_fundamentals_frame(),
            errors=(
                FundamentalsImportError(
                    row_number=None,
                    message=f"missing required columns: {', '.join(missing_columns)}",
                ),
            ),
        )

    universe_by_ticker = {member.ticker: member for member in universe}
    normalized_rows: list[dict[str, object]] = []

    for row_number, (_, row) in enumerate(raw.iterrows(), start=2):
        try:
            normalized_rows.append(_normalize_fundamentals_row(row, universe_by_ticker))
        except Exception as exc:
            errors.append(FundamentalsImportError(row_number=row_number, message=str(exc)))

    if not normalized_rows:
        return FundamentalsImportResult(
            records=empty_fundamentals_frame(),
            errors=tuple(errors)
            or (FundamentalsImportError(row_number=None, message="no rows normalized"),),
        )

    records = pd.DataFrame(normalized_rows)
    records = records.loc[:, list(FUNDAMENTALS_COLUMNS)]
    records = records.sort_values(["ticker", "period_end", "disclosure_timestamp"]).reset_index(
        drop=True
    )
    return FundamentalsImportResult(records=records, errors=tuple(errors))


def fundamentals_to_point_in_time_records(records: pd.DataFrame) -> list[PointInTimeRecord]:
    """Convert normalized fundamentals rows to validation point-in-time records."""

    _require_fundamentals_columns(
        records,
        ["ticker", "period_end", "disclosure_timestamp", "download_timestamp", "source"],
    )
    point_in_time_records: list[PointInTimeRecord] = []
    for index, row in records.iterrows():
        point_in_time_records.append(
            PointInTimeRecord(
                record_id=f"{row['ticker']}-{row['period_end']}",
                observation_period_end=str(row["period_end"]),
                publication_timestamp=str(row["disclosure_timestamp"])
                if pd.notna(row["disclosure_timestamp"])
                else None,
                download_timestamp=str(row["download_timestamp"])
                if pd.notna(row["download_timestamp"])
                else None,
                source=str(row["source"]),
            )
        )
    return point_in_time_records


def write_fundamentals_schema(path: str | Path) -> Path:
    """Write a CSV header-only schema file for manual data preparation."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=list(FUNDAMENTALS_COLUMNS)).to_csv(output_path, index=False)
    return output_path


def empty_fundamentals_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(FUNDAMENTALS_COLUMNS))


def _normalize_fundamentals_row(
    row: pd.Series,
    universe_by_ticker: dict[str, UniverseMember],
) -> dict[str, object]:
    ticker = _required_text(row, "ticker").upper()
    member = universe_by_ticker.get(ticker)
    if member is None:
        raise FundamentalsSchemaError(f"{ticker} is not in the fixed universe")

    period_type = _required_text(row, "period_type").lower()
    if period_type not in ALLOWED_PERIOD_TYPES:
        raise FundamentalsSchemaError(
            f"period_type must be one of {', '.join(ALLOWED_PERIOD_TYPES)}"
        )

    disclosure_timestamp = _required_timestamp(row, "disclosure_timestamp")
    download_timestamp = _required_timestamp(row, "download_timestamp")
    period_end = _required_date(row, "period_end")

    normalized = {
        "ticker": ticker,
        "yahoo_symbol": member.yahoo_symbol,
        "sector": member.sector,
        "metric_profile": metric_profile_for_sector(member.sector),
        "period_end": period_end,
        "period_type": period_type,
        "disclosure_timestamp": disclosure_timestamp,
        "download_timestamp": download_timestamp,
        "source": _required_text(row, "source"),
        "currency": _optional_text(row, "currency", default="TRY"),
    }

    for column in NUMERIC_FUNDAMENTALS_COLUMNS:
        normalized[column] = _optional_number(row, column)

    return normalized


def metric_profile_for_sector(sector: str) -> str:
    """Return the metric profile used for sector-appropriate analysis."""

    lowered = sector.lower()
    if any(label in lowered for label in BANKING_SECTOR_LABELS):
        return "bank"
    return "industrial"


def _required_text(row: pd.Series, column: str) -> str:
    value = row.get(column)
    if pd.isna(value) or str(value).strip() == "":
        raise FundamentalsSchemaError(f"missing required value: {column}")
    return str(value).strip()


def _optional_text(row: pd.Series, column: str, default: str) -> str:
    value = row.get(column)
    if pd.isna(value) or str(value).strip() == "":
        return default
    return str(value).strip()


def _required_date(row: pd.Series, column: str) -> str:
    value = _required_text(row, column)
    try:
        return pd.to_datetime(value, errors="raise").date().isoformat()
    except Exception as exc:
        raise FundamentalsSchemaError(f"invalid date in {column}: {value}") from exc


def _required_timestamp(row: pd.Series, column: str) -> str:
    value = _required_text(row, column)
    try:
        return pd.to_datetime(value, utc=True, errors="raise").isoformat()
    except Exception as exc:
        raise FundamentalsSchemaError(f"invalid timestamp in {column}: {value}") from exc


def _optional_number(row: pd.Series, column: str) -> float | None:
    if column not in row.index:
        return None
    value = row.get(column)
    if pd.isna(value) or str(value).strip() == "":
        return None
    try:
        return float(value)
    except Exception as exc:
        raise FundamentalsSchemaError(f"invalid numeric value in {column}: {value}") from exc


def _require_fundamentals_columns(records: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in records.columns]
    if missing:
        raise FundamentalsSchemaError(
            f"fundamentals records missing required columns: {', '.join(missing)}"
        )
