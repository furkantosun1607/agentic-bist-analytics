"""Deterministic MCP-like tool surface for the research harness."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

from src.backtest import run_backtest
from src.context import (
    context_to_point_in_time_records,
    filter_context_for_decision,
    normalize_context,
)
from src.data import (
    MissingSymbol,
    UniverseMember,
    load_universe,
    read_price_cache,
)
from src.fundamentals import fundamentals_to_point_in_time_records
from src.indicators import add_all_indicators
from src.events import detect_all_events
from src.research import (
    run_quarterly_fundamentals,
    run_sector_catch_up,
    run_weekday_patterns,
)
from src.validation import (
    PointInTimeRecord,
    validate_market_dataset,
    validate_no_future_outcome_columns,
    validate_point_in_time_records,
)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    required_args: tuple[str, ...]


@dataclass(frozen=True)
class ToolResponse:
    status: str
    data: dict[str, object]
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class ToolInputError(ValueError):
    """Raised when a deterministic tool receives invalid input."""


ToolHandler = Callable[[dict[str, object]], ToolResponse]


TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="market_history",
        description="Return normalized market/index history metadata from cache or provided frames.",
        required_args=(),
    ),
    ToolSpec(
        name="indicators_events",
        description="Calculate indicators and technical events for one OHLCV frame.",
        required_args=("prices",),
    ),
    ToolSpec(
        name="sector_ranking",
        description="Run fixed-universe sector catch-up ranking.",
        required_args=("prices_by_symbol", "universe"),
    ),
    ToolSpec(
        name="weekday_test",
        description="Run weekday and multi-day pattern tests.",
        required_args=("prices_by_symbol",),
    ),
    ToolSpec(
        name="point_in_time_fundamentals",
        description="Validate and optionally analyze point-in-time fundamentals.",
        required_args=("fundamentals",),
    ),
    ToolSpec(
        name="context",
        description="Normalize and filter macro/news/video context by decision timestamp.",
        required_args=("context_records",),
    ),
    ToolSpec(
        name="backtest",
        description="Run point-in-time safe backtest with configured costs and benchmarks.",
        required_args=("signals", "prices_by_symbol"),
    ),
    ToolSpec(
        name="data_quality",
        description="Run market data and future-outcome feature quality checks.",
        required_args=(),
    ),
    ToolSpec(
        name="evidence_bundle",
        description="Build a source-linked evidence bundle from observed records.",
        required_args=("records",),
    ),
)


def list_tools() -> tuple[ToolSpec, ...]:
    """Return the deterministic tool registry."""

    return TOOL_SPECS


def call_tool(name: str, args: dict[str, object] | None = None) -> ToolResponse:
    """Execute one deterministic tool by name and return a structured response."""

    handlers: dict[str, ToolHandler] = {
        "market_history": market_history_tool,
        "indicators_events": indicators_events_tool,
        "sector_ranking": sector_ranking_tool,
        "weekday_test": weekday_test_tool,
        "point_in_time_fundamentals": point_in_time_fundamentals_tool,
        "context": context_tool,
        "backtest": backtest_tool,
        "data_quality": data_quality_tool,
        "evidence_bundle": evidence_bundle_tool,
    }
    handler = handlers.get(name)
    if handler is None:
        return ToolResponse(
            status="error",
            data={},
            errors=(f"unknown tool: {name}",),
        )

    try:
        return handler(args or {})
    except Exception as exc:
        return ToolResponse(status="error", data={}, errors=(str(exc),))


def market_history_tool(args: dict[str, object]) -> ToolResponse:
    """Return market history metadata from provided frames or cache files."""

    prices_by_symbol = _prices_by_symbol_from_args(args)
    if not prices_by_symbol:
        raise ToolInputError("market_history requires prices_by_symbol or cache_dir with symbols")

    summaries = []
    warnings: list[str] = []
    for symbol, prices in prices_by_symbol.items():
        try:
            _require_columns(prices, ["date", "close"], scope=symbol)
            dates = pd.to_datetime(prices["date"], errors="raise")
            summaries.append(
                {
                    "symbol": symbol,
                    "row_count": int(len(prices)),
                    "start_date": dates.min().date().isoformat(),
                    "end_date": dates.max().date().isoformat(),
                    "last_close": float(pd.to_numeric(prices["close"], errors="raise").iloc[-1]),
                    "source": _first_value(prices, "source"),
                    "download_timestamp": _first_value(prices, "download_timestamp"),
                }
            )
        except Exception as exc:
            warnings.append(f"{symbol}: {exc}")

    return ToolResponse(
        status="ok" if summaries else "warning",
        data={"symbols": summaries, "symbol_count": len(summaries)},
        warnings=tuple(warnings),
    )


def indicators_events_tool(args: dict[str, object]) -> ToolResponse:
    """Calculate indicators and deterministic event detections for one price frame."""

    prices = _required_frame(args, "prices")
    symbol = str(args.get("symbol") or _first_value(prices, "symbol") or "UNKNOWN")
    indicator_frame = add_all_indicators(prices)
    detection = detect_all_events(indicator_frame, symbol=symbol)
    latest = indicator_frame.tail(1).to_dict("records")

    return ToolResponse(
        status="ok",
        data={
            "symbol": symbol,
            "latest_indicators": _sanitize(latest[0] if latest else {}),
            "event_count": int(len(detection.events)),
            "events": _records(detection.events),
        },
        warnings=tuple(f"{error.detector}: {error.message}" for error in detection.errors),
    )


def sector_ranking_tool(args: dict[str, object]) -> ToolResponse:
    """Run sector catch-up analysis and return structured observations."""

    prices_by_symbol = _required_prices_by_symbol(args, "prices_by_symbol")
    universe = _universe_from_arg(args.get("universe"))
    result = run_sector_catch_up(
        prices_by_symbol=prices_by_symbol,
        universe=universe,
        lookback_days=int(args.get("lookback_days", 20)),
        horizons=tuple(int(value) for value in args.get("horizons", (5, 10, 20))),
    )
    observations = result.observations
    return ToolResponse(
        status="ok" if not observations.empty else "warning",
        data={
            "observation_count": int(len(observations)),
            "observations": _records(observations),
        },
        warnings=tuple(f"{error.scope}: {error.message}" for error in result.errors),
    )


def weekday_test_tool(args: dict[str, object]) -> ToolResponse:
    """Run weekday and multi-day pattern research."""

    result = run_weekday_patterns(
        prices_by_symbol=_required_prices_by_symbol(args, "prices_by_symbol"),
        benchmark_prices=args.get("benchmark_prices"),
        holding_days=tuple(int(value) for value in args.get("holding_days", (1, 2, 3, 4, 5))),
        trading_cost_bps=float(args.get("trading_cost_bps", 10.0)),
        slippage_bps=float(args.get("slippage_bps", 5.0)),
        regime_lookback_days=int(args.get("regime_lookback_days", 20)),
        unseen_start_date=args.get("unseen_start_date"),
    )
    return ToolResponse(
        status="ok" if not result.observations.empty else "warning",
        data={
            "observation_count": int(len(result.observations)),
            "summary": _records(result.summary),
        },
        warnings=tuple(f"{error.scope}: {error.message}" for error in result.errors),
    )


def point_in_time_fundamentals_tool(args: dict[str, object]) -> ToolResponse:
    """Validate fundamentals timestamps and optionally run fundamentals research."""

    fundamentals = _required_frame(args, "fundamentals")
    decision_timestamp = args.get("decision_timestamp")
    warnings: list[str] = []
    data: dict[str, object] = {
        "record_count": int(len(fundamentals)),
    }

    if decision_timestamp is not None:
        report = validate_point_in_time_records(
            fundamentals_to_point_in_time_records(fundamentals),
            str(decision_timestamp),
        )
        data["gate_status"] = report.gate_status
        data["issues"] = [asdict(issue) for issue in report.issues]

    if "prices_by_symbol" in args:
        result = run_quarterly_fundamentals(
            fundamentals=fundamentals,
            prices_by_symbol=_required_prices_by_symbol(args, "prices_by_symbol"),
            benchmark_prices=args.get("benchmark_prices"),
            horizons=tuple(int(value) for value in args.get("horizons", (1, 5, 20))),
        )
        data["observation_count"] = int(len(result.observations))
        data["summary"] = _records(result.summary)
        warnings.extend(f"{error.scope}: {error.message}" for error in result.errors)

    return ToolResponse(status="ok", data=data, warnings=tuple(warnings))


def context_tool(args: dict[str, object]) -> ToolResponse:
    """Normalize and filter macro/news/video context records."""

    raw_context = _required_frame(args, "context_records")
    normalized = normalize_context(raw_context)
    records = normalized.records

    if args.get("decision_timestamp") is not None and not records.empty:
        records = filter_context_for_decision(records, str(args["decision_timestamp"]))
        report = validate_point_in_time_records(
            context_to_point_in_time_records(records),
            str(args["decision_timestamp"]),
        )
        gate_status = report.gate_status
        issues = [asdict(issue) for issue in report.issues]
    else:
        gate_status = "NOT_EVALUATED"
        issues = []

    return ToolResponse(
        status="ok" if not records.empty else "warning",
        data={
            "record_count": int(len(records)),
            "records": _records(records),
            "gate_status": gate_status,
            "issues": issues,
        },
        warnings=tuple(f"row {error.row_number}: {error.message}" for error in normalized.errors),
    )


def backtest_tool(args: dict[str, object]) -> ToolResponse:
    """Run the deterministic backtest engine."""

    result = run_backtest(
        signals=_required_frame(args, "signals"),
        prices_by_symbol=_required_prices_by_symbol(args, "prices_by_symbol"),
        benchmark_prices=args.get("benchmark_prices"),
        sector_benchmark_prices=args.get("sector_benchmark_prices"),
        symbol_to_sector=args.get("symbol_to_sector"),
        default_horizon=int(args.get("default_horizon", 5)),
        trading_cost_bps=float(args.get("trading_cost_bps", 10.0)),
        slippage_bps=float(args.get("slippage_bps", 5.0)),
    )
    return ToolResponse(
        status="ok" if not result.trades.empty else "warning",
        data={
            "trade_count": int(len(result.trades[result.trades["status"] == "ok"]))
            if not result.trades.empty
            else 0,
            "trades": _records(result.trades),
            "summary": _records(result.summary),
        },
        warnings=tuple(f"{error.scope}: {error.message}" for error in result.errors),
    )


def data_quality_tool(args: dict[str, object]) -> ToolResponse:
    """Run deterministic data-quality checks."""

    issues = []
    warnings: list[str] = []

    if "prices_by_symbol" in args:
        prices_by_symbol = _required_prices_by_symbol(args, "prices_by_symbol")
        expected_symbols = args.get("expected_symbols", prices_by_symbol.keys())
        missing_symbols = tuple(
            MissingSymbol(symbol=str(item["symbol"]), reason=str(item["reason"]))
            if isinstance(item, dict)
            else item
            for item in args.get("missing_symbols", ())
        )
        report = validate_market_dataset(
            prices_by_symbol=prices_by_symbol,
            expected_symbols=expected_symbols,
            missing_symbols=missing_symbols,
            warn_on_small_sample_below=int(args.get("warn_on_small_sample_below", 20)),
        )
        issues.extend(asdict(issue) for issue in report.issues)
        gate_status = report.gate_status
    else:
        gate_status = "NOT_EVALUATED"
        warnings.append("prices_by_symbol not provided")

    if "feature_columns" in args:
        report = validate_no_future_outcome_columns(args["feature_columns"])
        issues.extend(asdict(issue) for issue in report.issues)
        if report.has_blocking_issues:
            gate_status = report.gate_status

    return ToolResponse(
        status="ok" if gate_status != "ANALYSIS_UNSAFE" else "warning",
        data={"gate_status": gate_status, "issues": issues},
        warnings=tuple(warnings),
    )


def evidence_bundle_tool(args: dict[str, object]) -> ToolResponse:
    """Build a source-linked evidence bundle from observed rows."""

    records = _required_frame(args, "records")
    feature_columns = list(args.get("feature_columns", ()))
    source_columns = list(args.get("source_columns", ("source", "known_at", "date")))
    if not feature_columns:
        raise ToolInputError("evidence_bundle requires feature_columns")

    _require_columns(records, feature_columns, scope="evidence records")
    available_source_columns = [column for column in source_columns if column in records.columns]
    evidence = []
    for index, row in records.iterrows():
        observed_features = {
            column: _sanitize(row[column])
            for column in feature_columns
            if column in records.columns
        }
        sources = {
            column: _sanitize(row[column])
            for column in available_source_columns
            if pd.notna(row[column])
        }
        evidence.append(
            {
                "evidence_id": str(row.get("signal_id") or row.get("context_id") or index),
                "observed_features": observed_features,
                "sources": sources,
            }
        )

    return ToolResponse(
        status="ok",
        data={"evidence_count": len(evidence), "evidence": evidence},
    )


def _prices_by_symbol_from_args(args: dict[str, object]) -> dict[str, pd.DataFrame]:
    if "prices_by_symbol" in args:
        return _required_prices_by_symbol(args, "prices_by_symbol")

    cache_dir = args.get("cache_dir")
    symbols = args.get("symbols")
    if cache_dir is None or symbols is None:
        return {}

    return {str(symbol): read_price_cache(Path(cache_dir), str(symbol)) for symbol in symbols}


def _required_prices_by_symbol(args: dict[str, object], key: str) -> dict[str, pd.DataFrame]:
    value = args.get(key)
    if not isinstance(value, dict) or not value:
        raise ToolInputError(f"{key} must be a non-empty dict of DataFrames")
    for symbol, frame in value.items():
        if not isinstance(frame, pd.DataFrame):
            raise ToolInputError(f"{key}.{symbol} must be a DataFrame")
    return value


def _required_frame(args: dict[str, object], key: str) -> pd.DataFrame:
    value = args.get(key)
    if not isinstance(value, pd.DataFrame):
        raise ToolInputError(f"{key} must be a DataFrame")
    return value


def _universe_from_arg(value: object) -> list[UniverseMember]:
    if value is None:
        return load_universe()
    if isinstance(value, list) and all(isinstance(item, UniverseMember) for item in value):
        return value
    if isinstance(value, pd.DataFrame):
        _require_columns(value, ["ticker", "yahoo_symbol", "sector"], scope="universe")
        return [
            UniverseMember(
                ticker=str(row["ticker"]),
                yahoo_symbol=str(row["yahoo_symbol"]),
                sector=str(row["sector"]),
            )
            for _, row in value.iterrows()
        ]
    raise ToolInputError("universe must be a list[UniverseMember] or DataFrame")


def _records(frame: pd.DataFrame) -> list[dict[str, object]]:
    return [_sanitize(record) for record in frame.to_dict("records")]


def _sanitize(value):
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize(item) for item in value)
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def _first_value(frame: pd.DataFrame, column: str) -> object | None:
    if column not in frame.columns or frame[column].dropna().empty:
        return None
    return _sanitize(frame[column].dropna().iloc[0])


def _require_columns(frame: pd.DataFrame, columns: list[str], scope: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ToolInputError(f"{scope} missing required columns: {', '.join(missing)}")
