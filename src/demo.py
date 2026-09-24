"""Offline classroom demo orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data import load_universe, validate_universe
from src.reporting import (
    validate_report_manifest,
    write_final_technical_report,
    write_report_index,
)
from src.settings import DEFAULT_SETTINGS_PATH, Settings, load_settings


PASS = "pass"
WARNING = "warning"
FAIL = "fail"


@dataclass(frozen=True)
class DemoCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class DemoResult:
    exit_code: int
    summary_path: Path
    checks: tuple[DemoCheck, ...]

    @property
    def has_failures(self) -> bool:
        return any(check.status == FAIL for check in self.checks)


def run_offline_demo(
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
    output_path: str | Path | None = None,
    strict_cache: bool = False,
) -> DemoResult:
    """Run a no-network demo and write a compact status report."""

    checks: list[DemoCheck] = []
    settings: Settings | None = None
    summary_path = Path(output_path) if output_path else Path("reports/demo_summary.md")

    try:
        settings = load_settings(settings_path)
        summary_path = Path(output_path) if output_path else settings.paths.reports_dir / "demo_summary.md"
        checks.append(
            DemoCheck(
                name="settings",
                status=PASS,
                detail=f"loaded {Path(settings_path)}",
            )
        )
    except Exception as exc:
        checks.append(DemoCheck(name="settings", status=FAIL, detail=str(exc)))

    if settings is not None:
        checks.extend(_check_universe(settings))
        checks.extend(_check_reports())
        checks.append(_check_cache(settings, strict_cache=strict_cache))

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(_render_demo_summary(checks), encoding="utf-8")

    exit_code = 1 if any(check.status == FAIL for check in checks) else 0
    return DemoResult(
        exit_code=exit_code,
        summary_path=summary_path,
        checks=tuple(checks),
    )


def _check_universe(settings: Settings) -> list[DemoCheck]:
    try:
        members = load_universe(settings.paths.universe)
        errors = validate_universe(
            members,
            expected_size=settings.validation.expected_universe_size,
        )
    except Exception as exc:
        return [DemoCheck(name="universe", status=FAIL, detail=str(exc))]

    if errors:
        return [DemoCheck(name="universe", status=FAIL, detail="; ".join(errors))]
    return [
        DemoCheck(
            name="universe",
            status=PASS,
            detail=f"{len(members)} fixed symbols validated",
        )
    ]


def _check_reports() -> list[DemoCheck]:
    checks: list[DemoCheck] = []
    try:
        report_index = write_report_index()
        final_report = write_final_technical_report()
        checks.append(
            DemoCheck(
                name="report_generation",
                status=PASS,
                detail=f"wrote {_display_path(report_index)} and {_display_path(final_report)}",
            )
        )
        manifest_errors = validate_report_manifest()
    except Exception as exc:
        return [DemoCheck(name="report_generation", status=FAIL, detail=str(exc))]

    if manifest_errors:
        checks.append(
            DemoCheck(
                name="report_manifest",
                status=FAIL,
                detail="; ".join(manifest_errors),
            )
        )
    else:
        checks.append(
            DemoCheck(
                name="report_manifest",
                status=PASS,
                detail="all report metadata paths are present",
            )
        )
    return checks


def _check_cache(settings: Settings, strict_cache: bool) -> DemoCheck:
    try:
        cache_files = sorted(settings.paths.cache_dir.glob("*.csv"))
    except Exception as exc:
        return DemoCheck(name="cache", status=FAIL, detail=str(exc))

    if cache_files:
        return DemoCheck(
            name="cache",
            status=PASS,
            detail=(
                f"{len(cache_files)} cached market files found in "
                f"{_display_path(settings.paths.cache_dir)}"
            ),
        )

    status = FAIL if strict_cache else WARNING
    return DemoCheck(
        name="cache",
        status=status,
        detail=(
            "no cached market files found; demo still runs in infrastructure-only mode"
        ),
    )


def _render_demo_summary(checks: list[DemoCheck]) -> str:
    lines = [
        "# Classroom Demo Summary",
        "",
        "Command: `python -m scripts.demo --offline`",
        "",
        "This demo performs no network calls. It validates the fixed universe, regenerates the report index and final technical report, checks for an optional cached market dataset, and records whether the run is infrastructure-only.",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        lines.append(f"| {check.name} | {check.status} | {_escape_table(check.detail)} |")

    lines.extend(
        [
            "",
            "## Cached Dataset",
            "",
            "To populate a live cache before class, run `python -m scripts.fetch_market_data` with source access available. The offline demo command can then be rerun without live source availability and will read the cache status from `data/cache`.",
            "",
            "## Interpretation",
            "",
            "Warnings do not create measured financial findings. They identify missing live/cache inputs that must be populated before empirical return, risk or strategy-comparison claims can be made.",
            "",
        ]
    )
    return "\n".join(lines)


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
