"""Runtime configuration loading for the research harness."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    timezone: str


@dataclass(frozen=True)
class PathConfig:
    universe: Path
    cache_dir: Path
    reports_dir: Path
    notebooks_dir: Path


@dataclass(frozen=True)
class MarketDataConfig:
    benchmark_symbol: str
    price_source: str
    adjusted_price_policy: str
    start_date: str
    end_date: str | None


@dataclass(frozen=True)
class FundamentalsConfig:
    source: str
    output_path: Path
    synthetic_disclosure_lag_days: int
    synthetic_disclosure_time: str


@dataclass(frozen=True)
class BacktestConfig:
    entry_timing: str
    exit_timing: str
    trading_cost_bps: float
    slippage_bps: float
    horizons: tuple[int, ...]


@dataclass(frozen=True)
class ExperimentConfig:
    unseen_start_date: str | None
    regime_lookback_days: int


@dataclass(frozen=True)
class ValidationConfig:
    expected_universe_size: int
    block_on_future_leakage: bool
    block_on_critical_date_mismatch: bool
    warn_on_small_sample_below: int


@dataclass(frozen=True)
class OutputConfig:
    report_format: str
    decision_log_dir: Path


@dataclass(frozen=True)
class Settings:
    project: ProjectConfig
    paths: PathConfig
    market_data: MarketDataConfig
    fundamentals: FundamentalsConfig
    backtest: BacktestConfig
    experiment: ExperimentConfig
    validation: ValidationConfig
    outputs: OutputConfig


def load_settings(path: str | Path = DEFAULT_SETTINGS_PATH) -> Settings:
    """Load and normalize runtime settings from YAML."""

    settings_path = Path(path)
    with settings_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    return parse_settings(raw)


def parse_settings(raw: dict[str, Any]) -> Settings:
    """Convert a raw settings dictionary into typed settings."""

    project = raw.get("project", {})
    paths = raw.get("paths", {})
    market_data = raw.get("market_data", {})
    fundamentals = raw.get("fundamentals", {})
    backtest = raw.get("backtest", {})
    experiment = raw.get("experiment", {})
    validation = raw.get("validation", {})
    outputs = raw.get("outputs", {})

    return Settings(
        project=ProjectConfig(
            name=_required_str(project, "name"),
            timezone=_required_str(project, "timezone"),
        ),
        paths=PathConfig(
            universe=_project_path(_required_str(paths, "universe")),
            cache_dir=_project_path(_required_str(paths, "cache_dir")),
            reports_dir=_project_path(_required_str(paths, "reports_dir")),
            notebooks_dir=_project_path(_required_str(paths, "notebooks_dir")),
        ),
        market_data=MarketDataConfig(
            benchmark_symbol=_required_str(market_data, "benchmark_symbol"),
            price_source=_required_str(market_data, "price_source"),
            adjusted_price_policy=_required_str(market_data, "adjusted_price_policy"),
            start_date=_required_str(market_data, "start_date"),
            end_date=market_data.get("end_date"),
        ),
        fundamentals=FundamentalsConfig(
            source=_required_str(fundamentals, "source"),
            output_path=_project_path(_required_str(fundamentals, "output_path")),
            synthetic_disclosure_lag_days=_required_int(
                fundamentals, "synthetic_disclosure_lag_days"
            ),
            synthetic_disclosure_time=_required_str(
                fundamentals, "synthetic_disclosure_time"
            ),
        ),
        backtest=BacktestConfig(
            entry_timing=_required_str(backtest, "entry_timing"),
            exit_timing=_required_str(backtest, "exit_timing"),
            trading_cost_bps=_required_number(backtest, "trading_cost_bps"),
            slippage_bps=_required_number(backtest, "slippage_bps"),
            horizons=tuple(int(horizon) for horizon in backtest.get("horizons", [])),
        ),
        experiment=ExperimentConfig(
            unseen_start_date=experiment.get("unseen_start_date"),
            regime_lookback_days=_required_int(experiment, "regime_lookback_days"),
        ),
        validation=ValidationConfig(
            expected_universe_size=_required_int(validation, "expected_universe_size"),
            block_on_future_leakage=bool(validation.get("block_on_future_leakage")),
            block_on_critical_date_mismatch=bool(
                validation.get("block_on_critical_date_mismatch")
            ),
            warn_on_small_sample_below=_required_int(
                validation, "warn_on_small_sample_below"
            ),
        ),
        outputs=OutputConfig(
            report_format=_required_str(outputs, "report_format"),
            decision_log_dir=_project_path(_required_str(outputs, "decision_log_dir")),
        ),
    )


def _project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _required_str(section: dict[str, Any], key: str) -> str:
    value = section.get(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing required setting: {key}")
    return str(value)


def _required_number(section: dict[str, Any], key: str) -> float:
    value = section.get(key)
    if value is None:
        raise ValueError(f"missing required setting: {key}")
    return float(value)


def _required_int(section: dict[str, Any], key: str) -> int:
    value = section.get(key)
    if value is None:
        raise ValueError(f"missing required setting: {key}")
    return int(value)
