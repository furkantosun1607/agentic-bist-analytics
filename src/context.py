"""Point-in-time macro, news, and public-video context records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.validation import PointInTimeRecord


CONTEXT_COLUMNS = (
    "context_id",
    "context_type",
    "scope",
    "ticker",
    "sector",
    "indicator",
    "value",
    "unit",
    "observed_period_start",
    "observed_period_end",
    "publication_timestamp",
    "download_timestamp",
    "source",
    "source_url",
    "source_access",
    "title",
    "claim",
    "video_timestamp",
    "notes",
)
REQUIRED_CONTEXT_COLUMNS = (
    "context_id",
    "context_type",
    "scope",
    "observed_period_start",
    "observed_period_end",
    "publication_timestamp",
    "download_timestamp",
    "source",
    "source_access",
)
ALLOWED_CONTEXT_TYPES = ("macro", "news", "video")
ALLOWED_SOURCE_ACCESS = ("public", "licensed", "instructor_approved")
MACRO_INDICATORS = (
    "usd_try",
    "eur_try",
    "tcmb_policy_rate",
    "tuik_inflation",
    "fed_policy_rate",
)


@dataclass(frozen=True)
class ContextImportError:
    row_number: int | None
    message: str


@dataclass(frozen=True)
class ContextImportResult:
    records: pd.DataFrame
    errors: tuple[ContextImportError, ...]


class ContextSchemaError(ValueError):
    """Raised when context input cannot be normalized."""


def load_context_csv(path: str | Path) -> ContextImportResult:
    """Load context records from CSV into the normalized schema."""

    try:
        raw = pd.read_csv(path)
    except Exception as exc:
        return ContextImportResult(
            records=empty_context_frame(),
            errors=(ContextImportError(row_number=None, message=str(exc)),),
        )

    return normalize_context(raw)


def normalize_context(raw: pd.DataFrame) -> ContextImportResult:
    """Normalize macro/news/video context records with row-level errors."""

    if raw is None or raw.empty:
        return ContextImportResult(
            records=empty_context_frame(),
            errors=(ContextImportError(row_number=None, message="no context rows"),),
        )

    missing_columns = [column for column in REQUIRED_CONTEXT_COLUMNS if column not in raw.columns]
    if missing_columns:
        return ContextImportResult(
            records=empty_context_frame(),
            errors=(
                ContextImportError(
                    row_number=None,
                    message=f"missing required columns: {', '.join(missing_columns)}",
                ),
            ),
        )

    rows: list[dict[str, object]] = []
    errors: list[ContextImportError] = []
    for row_number, (_, row) in enumerate(raw.iterrows(), start=2):
        try:
            rows.append(_normalize_context_row(row))
        except Exception as exc:
            errors.append(ContextImportError(row_number=row_number, message=str(exc)))

    if not rows:
        return ContextImportResult(
            records=empty_context_frame(),
            errors=tuple(errors) or (ContextImportError(row_number=None, message="no rows normalized"),),
        )

    records = pd.DataFrame(rows).loc[:, list(CONTEXT_COLUMNS)]
    records = records.sort_values(["context_type", "observed_period_end", "context_id"])
    records = records.reset_index(drop=True)
    return ContextImportResult(records=records, errors=tuple(errors))


def context_to_point_in_time_records(records: pd.DataFrame) -> list[PointInTimeRecord]:
    """Convert normalized context rows to validation point-in-time records."""

    _require_context_columns(
        records,
        [
            "context_id",
            "observed_period_end",
            "publication_timestamp",
            "download_timestamp",
            "source",
        ],
    )
    output: list[PointInTimeRecord] = []
    for _, row in records.iterrows():
        output.append(
            PointInTimeRecord(
                record_id=str(row["context_id"]),
                observation_period_end=str(row["observed_period_end"]),
                publication_timestamp=str(row["publication_timestamp"]),
                download_timestamp=str(row["download_timestamp"]),
                source=str(row["source"]),
            )
        )
    return output


def filter_context_for_decision(
    records: pd.DataFrame,
    decision_timestamp: str,
) -> pd.DataFrame:
    """Return records public by a historical decision timestamp."""

    _require_context_columns(records, ["publication_timestamp"])
    decision_time = pd.to_datetime(decision_timestamp, utc=True, errors="raise")
    publication_time = pd.to_datetime(records["publication_timestamp"], utc=True, errors="raise")
    return records.loc[publication_time <= decision_time].copy().reset_index(drop=True)


def write_context_schema(path: str | Path) -> Path:
    """Write a CSV header-only schema file for manual context preparation."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=list(CONTEXT_COLUMNS)).to_csv(output_path, index=False)
    return output_path


def empty_context_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(CONTEXT_COLUMNS))


def _normalize_context_row(row: pd.Series) -> dict[str, object]:
    context_type = _required_text(row, "context_type").lower()
    if context_type not in ALLOWED_CONTEXT_TYPES:
        raise ContextSchemaError(
            f"context_type must be one of {', '.join(ALLOWED_CONTEXT_TYPES)}"
        )

    source_access = _required_text(row, "source_access").lower()
    if source_access not in ALLOWED_SOURCE_ACCESS:
        raise ContextSchemaError(
            f"source_access must be one of {', '.join(ALLOWED_SOURCE_ACCESS)}"
        )

    record = {
        "context_id": _required_text(row, "context_id"),
        "context_type": context_type,
        "scope": _required_text(row, "scope").lower(),
        "ticker": _optional_text(row, "ticker"),
        "sector": _optional_text(row, "sector"),
        "indicator": _optional_text(row, "indicator"),
        "value": _optional_number(row, "value"),
        "unit": _optional_text(row, "unit"),
        "observed_period_start": _required_date(row, "observed_period_start"),
        "observed_period_end": _required_date(row, "observed_period_end"),
        "publication_timestamp": _required_timestamp(row, "publication_timestamp"),
        "download_timestamp": _required_timestamp(row, "download_timestamp"),
        "source": _required_text(row, "source"),
        "source_url": _optional_text(row, "source_url"),
        "source_access": source_access,
        "title": _optional_text(row, "title"),
        "claim": _optional_text(row, "claim"),
        "video_timestamp": _optional_text(row, "video_timestamp"),
        "notes": _optional_text(row, "notes"),
    }

    _validate_context_type_specific_fields(record)
    return record


def _validate_context_type_specific_fields(record: dict[str, object]) -> None:
    context_type = str(record["context_type"])
    if context_type == "macro":
        indicator = str(record["indicator"])
        if indicator not in MACRO_INDICATORS:
            raise ContextSchemaError(
                f"macro indicator must be one of {', '.join(MACRO_INDICATORS)}"
            )
        if record["value"] is None:
            raise ContextSchemaError("macro records require numeric value")
        return

    if not record["title"]:
        raise ContextSchemaError(f"{context_type} records require title")
    if not record["claim"]:
        raise ContextSchemaError(f"{context_type} records require claim")
    if not record["source_url"]:
        raise ContextSchemaError(f"{context_type} records require source_url")
    if context_type == "video" and not record["video_timestamp"]:
        raise ContextSchemaError("video records require video_timestamp")


def _required_text(row: pd.Series, column: str) -> str:
    value = row.get(column)
    if pd.isna(value) or str(value).strip() == "":
        raise ContextSchemaError(f"missing required value: {column}")
    return str(value).strip()


def _optional_text(row: pd.Series, column: str) -> str | None:
    if column not in row.index:
        return None
    value = row.get(column)
    if pd.isna(value) or str(value).strip() == "":
        return None
    return str(value).strip()


def _required_date(row: pd.Series, column: str) -> str:
    value = _required_text(row, column)
    try:
        return pd.to_datetime(value, errors="raise").date().isoformat()
    except Exception as exc:
        raise ContextSchemaError(f"invalid date in {column}: {value}") from exc


def _required_timestamp(row: pd.Series, column: str) -> str:
    value = _required_text(row, column)
    try:
        return pd.to_datetime(value, utc=True, errors="raise").isoformat()
    except Exception as exc:
        raise ContextSchemaError(f"invalid timestamp in {column}: {value}") from exc


def _optional_number(row: pd.Series, column: str) -> float | None:
    if column not in row.index:
        return None
    value = row.get(column)
    if pd.isna(value) or str(value).strip() == "":
        return None
    try:
        return float(value)
    except Exception as exc:
        raise ContextSchemaError(f"invalid numeric value in {column}: {value}") from exc


def _require_context_columns(records: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in records.columns]
    if missing:
        raise ContextSchemaError(f"context records missing required columns: {', '.join(missing)}")
