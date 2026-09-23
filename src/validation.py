"""Data quality and point-in-time safety checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

import pandas as pd

from src.data import MissingSymbol, PRICE_CACHE_COLUMNS


BLOCKING = "blocking"
WARNING = "warning"
INFO = "info"
ANALYSIS_SAFE = "ANALYSIS_SAFE"
ANALYSIS_UNSAFE = "ANALYSIS_UNSAFE"


@dataclass(frozen=True)
class QualityIssue:
    severity: str
    code: str
    message: str
    symbol: str | None = None


@dataclass(frozen=True)
class QualityReport:
    issues: tuple[QualityIssue, ...]

    @property
    def has_blocking_issues(self) -> bool:
        return any(issue.severity == BLOCKING for issue in self.issues)

    @property
    def gate_status(self) -> str:
        return ANALYSIS_UNSAFE if self.has_blocking_issues else ANALYSIS_SAFE

    def issues_by_severity(self, severity: str) -> tuple[QualityIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == severity)


@dataclass(frozen=True)
class PointInTimeRecord:
    record_id: str
    observation_period_end: str
    publication_timestamp: str | None
    download_timestamp: str | None
    source: str


def validate_price_history(
    prices: pd.DataFrame,
    symbol: str,
    warn_on_small_sample_below: int,
) -> QualityReport:
    """Validate one normalized OHLCV price history."""

    issues: list[QualityIssue] = []

    if prices.empty:
        return QualityReport(
            (
                QualityIssue(
                    severity=BLOCKING,
                    code="EMPTY_PRICE_HISTORY",
                    message="price history has no rows",
                    symbol=symbol,
                ),
            )
        )

    missing_columns = [column for column in PRICE_CACHE_COLUMNS if column not in prices.columns]
    if missing_columns:
        issues.append(
            QualityIssue(
                severity=BLOCKING,
                code="MISSING_PRICE_COLUMNS",
                message=f"missing columns: {', '.join(missing_columns)}",
                symbol=symbol,
            )
        )
        return QualityReport(tuple(issues))

    if len(prices) < warn_on_small_sample_below:
        issues.append(
            QualityIssue(
                severity=WARNING,
                code="SMALL_SAMPLE",
                message=(
                    f"price history has {len(prices)} rows, below "
                    f"{warn_on_small_sample_below}"
                ),
                symbol=symbol,
            )
        )

    dates = pd.to_datetime(prices["date"], errors="coerce")
    if dates.isna().any():
        issues.append(
            QualityIssue(
                severity=BLOCKING,
                code="INVALID_PRICE_DATE",
                message="one or more price dates could not be parsed",
                symbol=symbol,
            )
        )
    elif not dates.is_monotonic_increasing:
        issues.append(
            QualityIssue(
                severity=BLOCKING,
                code="NON_MONOTONIC_PRICE_DATES",
                message="price dates are not sorted in increasing order",
                symbol=symbol,
            )
        )

    if prices["date"].duplicated().any():
        issues.append(
            QualityIssue(
                severity=BLOCKING,
                code="DUPLICATE_PRICE_DATES",
                message="price history contains duplicate dates",
                symbol=symbol,
            )
        )

    for column in ("open", "high", "low", "close", "adj_close"):
        values = pd.to_numeric(prices[column], errors="coerce")
        if values.isna().any():
            issues.append(
                QualityIssue(
                    severity=BLOCKING,
                    code="INVALID_PRICE_VALUE",
                    message=f"{column} contains non-numeric values",
                    symbol=symbol,
                )
            )
        elif (values <= 0).any():
            issues.append(
                QualityIssue(
                    severity=BLOCKING,
                    code="NON_POSITIVE_PRICE",
                    message=f"{column} contains non-positive values",
                    symbol=symbol,
                )
            )

    high = pd.to_numeric(prices["high"], errors="coerce")
    low = pd.to_numeric(prices["low"], errors="coerce")
    if high.notna().all() and low.notna().all() and (high < low).any():
        issues.append(
            QualityIssue(
                severity=BLOCKING,
                code="HIGH_BELOW_LOW",
                message="one or more rows have high below low",
                symbol=symbol,
            )
        )

    volume = pd.to_numeric(prices["volume"], errors="coerce")
    if volume.isna().any() or (volume < 0).any():
        issues.append(
            QualityIssue(
                severity=BLOCKING,
                code="INVALID_VOLUME",
                message="volume contains non-numeric or negative values",
                symbol=symbol,
            )
        )

    issues.extend(_validate_download_timestamps(prices, symbol))
    return QualityReport(tuple(issues))


def validate_market_dataset(
    prices_by_symbol: dict[str, pd.DataFrame],
    expected_symbols: Iterable[str],
    missing_symbols: Iterable[MissingSymbol],
    warn_on_small_sample_below: int,
) -> QualityReport:
    """Validate all fetched market histories and missing-symbol metadata."""

    issues: list[QualityIssue] = []
    expected = set(expected_symbols)

    for missing in missing_symbols:
        issues.append(
            QualityIssue(
                severity=WARNING,
                code="MISSING_SYMBOL",
                message=missing.reason,
                symbol=missing.symbol,
            )
        )

    for symbol in sorted(expected - set(prices_by_symbol)):
        issues.append(
            QualityIssue(
                severity=WARNING,
                code="EXPECTED_SYMBOL_NOT_FETCHED",
                message="expected symbol was not fetched",
                symbol=symbol,
            )
        )

    for symbol, prices in prices_by_symbol.items():
        report = validate_price_history(prices, symbol, warn_on_small_sample_below)
        issues.extend(report.issues)

    return QualityReport(tuple(issues))


def validate_point_in_time_records(
    records: Iterable[PointInTimeRecord],
    decision_timestamp: str,
) -> QualityReport:
    """Ensure records were public by the historical decision time."""

    decision_time = _parse_datetime(decision_timestamp)
    issues: list[QualityIssue] = []

    for record in records:
        if not record.publication_timestamp:
            issues.append(
                QualityIssue(
                    severity=WARNING,
                    code="MISSING_PUBLICATION_TIMESTAMP",
                    message=(
                        f"{record.record_id} from {record.source} has no publication "
                        "timestamp"
                    ),
                )
            )
            continue

        publication_time = _parse_datetime(record.publication_timestamp)
        observation_end = _parse_date(record.observation_period_end)

        if publication_time > decision_time:
            issues.append(
                QualityIssue(
                    severity=BLOCKING,
                    code="FUTURE_INFORMATION_LEAKAGE",
                    message=(
                        f"{record.record_id} was published after the decision time"
                    ),
                )
            )

        if observation_end > publication_time.date():
            issues.append(
                QualityIssue(
                    severity=BLOCKING,
                    code="OBSERVATION_AFTER_PUBLICATION",
                    message=(
                        f"{record.record_id} observation period ends after publication"
                    ),
                )
            )

        if record.download_timestamp:
            download_time = _parse_datetime(record.download_timestamp)
            if download_time < publication_time:
                issues.append(
                    QualityIssue(
                        severity=BLOCKING,
                        code="DOWNLOAD_BEFORE_PUBLICATION",
                        message=f"{record.record_id} download precedes publication",
                    )
                )

    return QualityReport(tuple(issues))


def validate_no_future_outcome_columns(columns: Iterable[str]) -> QualityReport:
    """Block feature sets that include known future-outcome column names."""

    blocked_tokens = ("future", "forward", "next_", "lead_", "outcome")
    issues = [
        QualityIssue(
            severity=BLOCKING,
            code="FUTURE_OUTCOME_FEATURE",
            message=f"feature column appears to contain a future outcome: {column}",
        )
        for column in columns
        if any(token in column.lower() for token in blocked_tokens)
    ]
    return QualityReport(tuple(issues))


def _validate_download_timestamps(prices: pd.DataFrame, symbol: str) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    dates = pd.to_datetime(prices["date"], errors="coerce")
    downloads = pd.to_datetime(prices["download_timestamp"], errors="coerce", utc=True)

    if downloads.isna().any():
        issues.append(
            QualityIssue(
                severity=BLOCKING,
                code="INVALID_DOWNLOAD_TIMESTAMP",
                message="one or more download timestamps could not be parsed",
                symbol=symbol,
            )
        )
        return issues

    download_dates = downloads.dt.date
    if dates.notna().all() and (dates.dt.date > download_dates).any():
        issues.append(
            QualityIssue(
                severity=BLOCKING,
                code="PRICE_DATE_AFTER_DOWNLOAD",
                message="price observation date is after its download timestamp",
                symbol=symbol,
            )
        )

    return issues


def _parse_datetime(value: str) -> datetime:
    parsed = pd.to_datetime(value, utc=True, errors="raise")
    return parsed.to_pydatetime()


def _parse_date(value: str) -> date:
    return pd.to_datetime(value, errors="raise").date()
