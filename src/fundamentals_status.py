"""Fundamentals import coverage and readiness status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data import DEFAULT_UNIVERSE_PATH, load_universe
from src.fundamentals import (
    FUNDAMENTALS_COLUMNS,
    NUMERIC_FUNDAMENTALS_COLUMNS,
    fundamentals_to_point_in_time_records,
    load_fundamentals_csv,
    write_fundamentals_schema,
)
from src.settings import PROJECT_ROOT
from src.validation import ANALYSIS_SAFE, validate_point_in_time_records


DEFAULT_FUNDAMENTALS_INPUT_PATH = PROJECT_ROOT / "data" / "fundamentals" / "fundamentals.csv"
DEFAULT_FUNDAMENTALS_STATUS_PATH = PROJECT_ROOT / "reports" / "fundamentals_import_status.md"
DEFAULT_FUNDAMENTALS_TEMPLATE_PATH = PROJECT_ROOT / "config" / "fundamentals_template.csv"


@dataclass(frozen=True)
class FundamentalsCoverageRow:
    ticker: str
    metric_profile: str
    record_count: int
    first_period_end: str | None
    latest_period_end: str | None
    latest_disclosure_timestamp: str | None
    populated_numeric_fields: tuple[str, ...]


@dataclass(frozen=True)
class FundamentalsStatusResult:
    status: str
    input_path: Path
    report_path: Path
    valid_rows: int
    error_count: int
    universe_coverage: int
    point_in_time_status: str | None
    coverage_rows: tuple[FundamentalsCoverageRow, ...]


def audit_fundamentals_import(
    input_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
    output_path: str | Path = DEFAULT_FUNDAMENTALS_STATUS_PATH,
    universe_path: str | Path = DEFAULT_UNIVERSE_PATH,
    decision_timestamp: str | None = None,
    template_path: str | Path = DEFAULT_FUNDAMENTALS_TEMPLATE_PATH,
) -> FundamentalsStatusResult:
    """Audit fundamentals import readiness and write a status report."""

    source_path = Path(input_path)
    write_fundamentals_schema(template_path)
    universe = load_universe(universe_path)

    if not source_path.exists():
        result = FundamentalsStatusResult(
            status="blocked_missing_fundamentals_csv",
            input_path=source_path,
            report_path=Path(output_path),
            valid_rows=0,
            error_count=0,
            universe_coverage=0,
            point_in_time_status=None,
            coverage_rows=(),
        )
        write_fundamentals_status_report(result, (), output_path)
        return result

    imported = load_fundamentals_csv(source_path, universe)
    coverage = summarize_fundamentals_coverage(imported.records)
    point_status = None
    if not imported.records.empty:
        records = fundamentals_to_point_in_time_records(imported.records)
        decision = decision_timestamp or _latest_download_timestamp(imported.records)
        point_status = validate_point_in_time_records(records, decision).gate_status

    status = _status_from_import(
        valid_rows=len(imported.records),
        error_count=len(imported.errors),
        point_in_time_status=point_status,
    )
    result = FundamentalsStatusResult(
        status=status,
        input_path=source_path,
        report_path=Path(output_path),
        valid_rows=len(imported.records),
        error_count=len(imported.errors),
        universe_coverage=len({row.ticker for row in coverage}),
        point_in_time_status=point_status,
        coverage_rows=coverage,
    )
    write_fundamentals_status_report(result, imported.errors, output_path)
    return result


def summarize_fundamentals_coverage(records: pd.DataFrame) -> tuple[FundamentalsCoverageRow, ...]:
    """Summarize valid fundamentals coverage by ticker."""

    if records is None or records.empty:
        return ()
    rows: list[FundamentalsCoverageRow] = []
    for ticker, group in records.groupby("ticker"):
        periods = pd.to_datetime(group["period_end"], errors="coerce")
        disclosures = pd.to_datetime(group["disclosure_timestamp"], utc=True, errors="coerce")
        populated = tuple(
            column
            for column in NUMERIC_FUNDAMENTALS_COLUMNS
            if column in group.columns and group[column].notna().any()
        )
        rows.append(
            FundamentalsCoverageRow(
                ticker=str(ticker),
                metric_profile=str(group["metric_profile"].iloc[0]),
                record_count=len(group),
                first_period_end=periods.min().date().isoformat() if periods.notna().any() else None,
                latest_period_end=periods.max().date().isoformat() if periods.notna().any() else None,
                latest_disclosure_timestamp=disclosures.max().isoformat()
                if disclosures.notna().any()
                else None,
                populated_numeric_fields=populated,
            )
        )
    return tuple(sorted(rows, key=lambda row: row.ticker))


def write_fundamentals_status_report(
    result: FundamentalsStatusResult,
    errors,
    output_path: str | Path = DEFAULT_FUNDAMENTALS_STATUS_PATH,
) -> Path:
    """Write fundamentals import readiness report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Fundamentals Import Status",
        "",
        f"Status: `{result.status}`",
        "",
        f"Expected local CSV: `{_display_path(result.input_path)}`",
        f"Schema template: `{_display_path(DEFAULT_FUNDAMENTALS_TEMPLATE_PATH)}`",
        f"Valid rows: {result.valid_rows}",
        f"Import errors: {result.error_count}",
        f"Universe ticker coverage: {result.universe_coverage}",
        f"Point-in-time gate: `{result.point_in_time_status or 'not_run'}`",
        "",
        "## User Decision Needed"
        if result.status == "blocked_missing_fundamentals_csv"
        else "## Current Source Decision",
        "",
        "- Local source is the instructor-approved yfinance fallback, written to `data/fundamentals/fundamentals.csv`.",
        "- Treat synthetic disclosure timestamps as conservative project assumptions, not exact KAP publication times.",
        "- If no valid CSV is available in a future run, quarterly fundamentals must remain `inconclusive`.",
        "",
        "## Coverage",
        "",
        "| Ticker | Profile | Records | First period | Latest period | Latest disclosure | Populated numeric fields |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    if result.coverage_rows:
        for row in result.coverage_rows:
            lines.append(
                f"| {row.ticker} | {row.metric_profile} | {row.record_count} | "
                f"{row.first_period_end or 'n/a'} | {row.latest_period_end or 'n/a'} | "
                f"{row.latest_disclosure_timestamp or 'n/a'} | "
                f"{', '.join(row.populated_numeric_fields) or 'none'} |"
            )
    else:
        lines.append("| n/a | n/a | 0 | n/a | n/a | n/a | none |")

    if errors:
        lines.extend(["", "## Import Errors", ""])
        for error in errors:
            row_label = f"row {error.row_number}" if error.row_number else "file"
            lines.append(f"- `{row_label}`: {error.message}")

    lines.extend(
        [
            "",
            "Limitations:",
            "- Fundamentals data is an external source artifact and is not committed.",
            "- Current yfinance fallback uses synthetic disclosure timestamps: period_end plus the configured conservative lag.",
            "- This report does not create measured quarterly findings by itself.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _status_from_import(
    valid_rows: int,
    error_count: int,
    point_in_time_status: str | None,
) -> str:
    if valid_rows == 0:
        return "blocked_no_valid_fundamentals"
    if point_in_time_status != ANALYSIS_SAFE:
        return "blocked_point_in_time_unsafe"
    if error_count:
        return "ready_with_import_warnings"
    return "ready"


def _latest_download_timestamp(records: pd.DataFrame) -> str:
    parsed = pd.to_datetime(records["download_timestamp"], utc=True, errors="raise")
    return parsed.max().isoformat()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
