"""Macro context import coverage and readiness status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.context import (
    MACRO_INDICATORS,
    context_to_point_in_time_records,
    load_context_csv,
    write_context_schema,
)
from src.settings import PROJECT_ROOT
from src.validation import ANALYSIS_SAFE, validate_point_in_time_records


DEFAULT_MACRO_CONTEXT_INPUT_PATH = PROJECT_ROOT / "data" / "macro" / "macro_context.csv"
DEFAULT_MACRO_CONTEXT_STATUS_PATH = PROJECT_ROOT / "reports" / "macro_context_status.md"
DEFAULT_CONTEXT_TEMPLATE_PATH = PROJECT_ROOT / "config" / "context_template.csv"


@dataclass(frozen=True)
class MacroIndicatorCoverageRow:
    indicator: str
    record_count: int
    first_observed_period_end: str | None
    latest_observed_period_end: str | None
    latest_publication_timestamp: str | None
    sources: tuple[str, ...]
    source_access: tuple[str, ...]


@dataclass(frozen=True)
class MacroContextStatusResult:
    status: str
    input_path: Path
    report_path: Path
    valid_macro_rows: int
    import_errors: int
    indicator_coverage: tuple[MacroIndicatorCoverageRow, ...]
    missing_indicators: tuple[str, ...]
    point_in_time_status: str | None


def audit_macro_context(
    input_path: str | Path = DEFAULT_MACRO_CONTEXT_INPUT_PATH,
    output_path: str | Path = DEFAULT_MACRO_CONTEXT_STATUS_PATH,
    decision_timestamp: str | None = None,
    template_path: str | Path = DEFAULT_CONTEXT_TEMPLATE_PATH,
) -> MacroContextStatusResult:
    """Audit local macro context readiness and write a status report."""

    source_path = Path(input_path)
    write_context_schema(template_path)

    if not source_path.exists():
        result = MacroContextStatusResult(
            status="blocked_missing_macro_context_csv",
            input_path=source_path,
            report_path=Path(output_path),
            valid_macro_rows=0,
            import_errors=0,
            indicator_coverage=(),
            missing_indicators=tuple(MACRO_INDICATORS),
            point_in_time_status=None,
        )
        write_macro_context_status_report(result, (), output_path)
        return result

    imported = load_context_csv(source_path)
    macro_records = _macro_records(imported.records)
    coverage = summarize_macro_indicator_coverage(macro_records)
    missing = tuple(
        indicator for indicator in MACRO_INDICATORS if indicator not in {row.indicator for row in coverage}
    )
    point_status = None
    if not macro_records.empty:
        decision = decision_timestamp or _latest_download_timestamp(macro_records)
        point_status = validate_point_in_time_records(
            context_to_point_in_time_records(macro_records),
            decision,
        ).gate_status

    result = MacroContextStatusResult(
        status=_status_from_import(
            valid_macro_rows=len(macro_records),
            import_errors=len(imported.errors),
            missing_indicators=missing,
            point_in_time_status=point_status,
        ),
        input_path=source_path,
        report_path=Path(output_path),
        valid_macro_rows=len(macro_records),
        import_errors=len(imported.errors),
        indicator_coverage=coverage,
        missing_indicators=missing,
        point_in_time_status=point_status,
    )
    write_macro_context_status_report(result, imported.errors, output_path)
    return result


def summarize_macro_indicator_coverage(
    records: pd.DataFrame,
) -> tuple[MacroIndicatorCoverageRow, ...]:
    """Summarize macro context coverage by indicator."""

    if records is None or records.empty:
        return ()

    rows: list[MacroIndicatorCoverageRow] = []
    for indicator, group in records.groupby("indicator"):
        observed_ends = pd.to_datetime(group["observed_period_end"], errors="coerce")
        publications = pd.to_datetime(group["publication_timestamp"], utc=True, errors="coerce")
        rows.append(
            MacroIndicatorCoverageRow(
                indicator=str(indicator),
                record_count=len(group),
                first_observed_period_end=observed_ends.min().date().isoformat()
                if observed_ends.notna().any()
                else None,
                latest_observed_period_end=observed_ends.max().date().isoformat()
                if observed_ends.notna().any()
                else None,
                latest_publication_timestamp=publications.max().isoformat()
                if publications.notna().any()
                else None,
                sources=tuple(sorted(str(value) for value in group["source"].dropna().unique())),
                source_access=tuple(
                    sorted(str(value) for value in group["source_access"].dropna().unique())
                ),
            )
        )
    return tuple(sorted(rows, key=lambda row: row.indicator))


def write_macro_context_status_report(
    result: MacroContextStatusResult,
    errors,
    output_path: str | Path = DEFAULT_MACRO_CONTEXT_STATUS_PATH,
) -> Path:
    """Write macro context readiness report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Macro Context Status",
        "",
        f"Status: `{result.status}`",
        "",
        f"Expected local CSV: `{_display_path(result.input_path)}`",
        f"Schema template: `{_display_path(DEFAULT_CONTEXT_TEMPLATE_PATH)}`",
        f"Valid macro rows: {result.valid_macro_rows}",
        f"Import errors: {result.import_errors}",
        f"Required indicators: {', '.join(MACRO_INDICATORS)}",
        f"Missing indicators: {', '.join(result.missing_indicators) or 'none'}",
        f"Point-in-time gate: `{result.point_in_time_status or 'not_run'}`",
        "",
        "## User Action",
        "",
        "- Provide `data/macro/macro_context.csv` in the shared context schema, or approve automated fetching where source access allows it.",
        "- Include publication timestamps; observed period dates alone are not enough for point-in-time analysis.",
        "- If an indicator cannot be sourced, keep it visible as a source gap instead of inventing values.",
        "",
        "## Coverage",
        "",
        "| Indicator | Records | First observed | Latest observed | Latest publication | Sources | Access |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
    ]
    if result.indicator_coverage:
        for row in result.indicator_coverage:
            lines.append(
                f"| {row.indicator} | {row.record_count} | "
                f"{row.first_observed_period_end or 'n/a'} | "
                f"{row.latest_observed_period_end or 'n/a'} | "
                f"{row.latest_publication_timestamp or 'n/a'} | "
                f"{', '.join(row.sources) or 'none'} | "
                f"{', '.join(row.source_access) or 'none'} |"
            )
    else:
        lines.append("| n/a | 0 | n/a | n/a | n/a | none | none |")

    if errors:
        lines.extend(["", "## Import Errors", ""])
        for error in errors:
            row_label = f"row {error.row_number}" if error.row_number else "file"
            lines.append(f"- `{row_label}`: {error.message}")

    lines.extend(
        [
            "",
            "Limitations:",
            "- Macro source exports are local artifacts and are not committed.",
            "- RSS macro alias context does not replace numeric macro records.",
            "- This report does not create measured macro findings by itself.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _macro_records(records: pd.DataFrame) -> pd.DataFrame:
    if records is None or records.empty:
        return pd.DataFrame(columns=getattr(records, "columns", []))
    return records.loc[records["context_type"] == "macro"].copy().reset_index(drop=True)


def _status_from_import(
    valid_macro_rows: int,
    import_errors: int,
    missing_indicators: tuple[str, ...],
    point_in_time_status: str | None,
) -> str:
    if valid_macro_rows == 0:
        return "blocked_no_valid_macro_context"
    if point_in_time_status != ANALYSIS_SAFE:
        return "blocked_point_in_time_unsafe"
    if missing_indicators:
        return "ready_with_source_gaps"
    if import_errors:
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
