"""Strategy variant comparison A-E."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.evidence import EvidenceBundle, build_evidence_bundle
from src.backtest import BACKTEST_SUMMARY_COLUMNS, run_backtest
from src.validation import BLOCKING, WARNING, QualityIssue, QualityReport


VARIANT_BACKTEST_SUMMARY_COLUMNS = tuple(
    column for column in BACKTEST_SUMMARY_COLUMNS if column != "status"
)
VARIANT_SUMMARY_COLUMNS = (
    "variant",
    "description",
    "status",
    "components",
    "missing_components",
    "data_start",
    "data_end",
    "trading_cost_bps",
    "slippage_bps",
    "rss_context_status",
    "rss_context_evidence_count",
    "rss_context_source_count",
    "rss_context_latest_timestamp",
    "rss_context_warnings",
    "rss_context_evidence_urls",
    *VARIANT_BACKTEST_SUMMARY_COLUMNS,
)
VARIANT_TRADE_COLUMNS = ("variant", "component", "component_signal_id")


@dataclass(frozen=True)
class StrategyVariant:
    name: str
    description: str
    required_components: tuple[str, ...]


@dataclass(frozen=True)
class StrategyVariantError:
    variant: str
    message: str


@dataclass(frozen=True)
class StrategyVariantComparisonResult:
    summary: pd.DataFrame
    trades: pd.DataFrame
    errors: tuple[StrategyVariantError, ...]


class StrategyVariantInputError(ValueError):
    """Raised when strategy variant inputs are structurally invalid."""


@dataclass(frozen=True)
class RssContextVariantStatus:
    status: str
    evidence_count: int
    source_count: int
    latest_timestamp: str | None
    evidence_urls: tuple[str, ...]
    warnings: tuple[str, ...]
    quality_report: QualityReport
    evidence_bundle: EvidenceBundle | None


STRATEGY_VARIANTS = (
    StrategyVariant(
        name="A",
        description="technical",
        required_components=("technical",),
    ),
    StrategyVariant(
        name="B",
        description="technical + sector",
        required_components=("technical", "sector"),
    ),
    StrategyVariant(
        name="C",
        description="technical + sector + fundamentals",
        required_components=("technical", "sector", "fundamentals"),
    ),
    StrategyVariant(
        name="D",
        description="technical + sector + fundamentals + macro",
        required_components=("technical", "sector", "fundamentals", "macro"),
    ),
    StrategyVariant(
        name="E",
        description="technical + sector + fundamentals + macro + verified news/video context",
        required_components=(
            "technical",
            "sector",
            "fundamentals",
            "macro",
            "news_video",
        ),
    ),
)


def compare_strategy_variants(
    signals_by_component: dict[str, pd.DataFrame],
    prices_by_symbol: dict[str, pd.DataFrame],
    benchmark_prices: pd.DataFrame | None = None,
    sector_benchmark_prices: dict[str, pd.DataFrame] | None = None,
    symbol_to_sector: dict[str, str] | None = None,
    rss_context: pd.DataFrame | str | Path | None = None,
    default_horizon: int = 5,
    trading_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> StrategyVariantComparisonResult:
    """Compare predefined strategy variants on the same data and cost assumptions."""

    _validate_inputs(signals_by_component, prices_by_symbol)
    data_start, data_end = _price_data_period(prices_by_symbol)
    rss_status = summarize_rss_context_for_variant_e(rss_context)
    summaries: list[dict[str, object]] = []
    trade_frames: list[pd.DataFrame] = []
    errors: list[StrategyVariantError] = []

    for variant in STRATEGY_VARIANTS:
        missing = _missing_components(signals_by_component, variant.required_components)
        if missing:
            summaries.append(
                _unavailable_summary_row(
                    variant=variant,
                    missing_components=missing,
                    data_start=data_start,
                    data_end=data_end,
                    trading_cost_bps=trading_cost_bps,
                    slippage_bps=slippage_bps,
                    rss_context=rss_status if variant.name == "E" else None,
                )
            )
            continue

        try:
            signals = _combine_variant_signals(signals_by_component, variant)
            result = run_backtest(
                signals=signals,
                prices_by_symbol=prices_by_symbol,
                benchmark_prices=benchmark_prices,
                sector_benchmark_prices=sector_benchmark_prices,
                symbol_to_sector=symbol_to_sector,
                default_horizon=default_horizon,
                trading_cost_bps=trading_cost_bps,
                slippage_bps=slippage_bps,
            )
            summaries.append(
                _summary_row_from_backtest(
                    variant=variant,
                    result_summary=result.summary,
                    data_start=data_start,
                    data_end=data_end,
                    trading_cost_bps=trading_cost_bps,
                    slippage_bps=slippage_bps,
                    rss_context=rss_status if variant.name == "E" else None,
                )
            )
            if not result.trades.empty:
                trades = result.trades.copy()
                trades.insert(0, "variant", variant.name)
                trades["component"] = trades["signal_id"].map(_component_from_signal_id)
                trades["component_signal_id"] = trades["signal_id"].map(
                    _component_signal_id_from_signal_id
                )
                trade_frames.append(trades)
            errors.extend(
                StrategyVariantError(variant=variant.name, message=f"{error.scope}: {error.message}")
                for error in result.errors
            )
        except Exception as exc:
            errors.append(StrategyVariantError(variant=variant.name, message=str(exc)))
            summaries.append(
                _error_summary_row(
                    variant=variant,
                    message=str(exc),
                    data_start=data_start,
                    data_end=data_end,
                    trading_cost_bps=trading_cost_bps,
                    slippage_bps=slippage_bps,
                    rss_context=rss_status if variant.name == "E" else None,
                )
            )

    trades = (
        pd.concat(trade_frames, ignore_index=True)
        if trade_frames
        else pd.DataFrame(columns=["variant"])
    )
    return StrategyVariantComparisonResult(
        summary=pd.DataFrame(summaries).loc[:, list(VARIANT_SUMMARY_COLUMNS)],
        trades=trades,
        errors=tuple(errors),
    )


def compare_strategy_variants_from_settings(
    signals_by_component: dict[str, pd.DataFrame],
    prices_by_symbol: dict[str, pd.DataFrame],
    settings,
    benchmark_prices: pd.DataFrame | None = None,
    sector_benchmark_prices: dict[str, pd.DataFrame] | None = None,
    symbol_to_sector: dict[str, str] | None = None,
    rss_context: pd.DataFrame | str | Path | None = None,
) -> StrategyVariantComparisonResult:
    """Compare strategy variants using configured horizon and cost assumptions."""

    if not settings.backtest.horizons:
        raise StrategyVariantInputError("settings.backtest.horizons must contain at least one value")

    return compare_strategy_variants(
        signals_by_component=signals_by_component,
        prices_by_symbol=prices_by_symbol,
        benchmark_prices=benchmark_prices,
        sector_benchmark_prices=sector_benchmark_prices,
        symbol_to_sector=symbol_to_sector,
        rss_context=rss_context,
        default_horizon=int(settings.backtest.horizons[0]),
        trading_cost_bps=float(settings.backtest.trading_cost_bps),
        slippage_bps=float(settings.backtest.slippage_bps),
    )


def write_strategy_variants_report(
    result: StrategyVariantComparisonResult,
    output_path: str | Path,
) -> Path:
    """Write a compact markdown report for strategy variant comparisons."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Strategy Variant Comparison A-E",
        "",
        "Variants:",
        "- A: technical",
        "- B: technical + sector",
        "- C: B + fundamentals",
        "- D: C + macro",
        "- E: D + verified news/video context",
        "",
        "RSS context policy:",
        "- RSS context metadata can make Variant E context availability explicit.",
        "- RSS context does not create trade signals by itself.",
        "- Future-dated or missing source metadata remains a warning/blocking quality issue.",
        "",
    ]
    if result.summary.empty:
        lines.extend(["Status: no variant summary generated.", ""])
    else:
        lines.extend(["## Summary", "", result.summary.to_markdown(index=False), ""])

    if result.errors:
        lines.extend(["## Errors", ""])
        for error in result.errors:
            lines.append(f"- `{error.variant}`: {error.message}")
        lines.append("")

    lines.extend(
        [
            "Limitations:",
            "- Missing-source variants are marked unavailable; values are not invented.",
            "- RSS news density is context evidence only and is not reported as a performance claim.",
            "- All variants use the same provided price data, benchmark hooks and cost assumptions.",
            "- This report is historical research infrastructure, not investment advice.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _validate_inputs(
    signals_by_component: dict[str, pd.DataFrame],
    prices_by_symbol: dict[str, pd.DataFrame],
) -> None:
    if not isinstance(signals_by_component, dict):
        raise StrategyVariantInputError("signals_by_component must be a dict")
    if not isinstance(prices_by_symbol, dict) or not prices_by_symbol:
        raise StrategyVariantInputError("prices_by_symbol must be a non-empty dict")
    for component, signals in signals_by_component.items():
        if not isinstance(signals, pd.DataFrame):
            raise StrategyVariantInputError(f"{component} signals must be a DataFrame")


def _missing_components(
    signals_by_component: dict[str, pd.DataFrame],
    required_components: tuple[str, ...],
) -> tuple[str, ...]:
    missing = []
    for component in required_components:
        signals = signals_by_component.get(component)
        if signals is None or signals.empty:
            missing.append(component)
    return tuple(missing)


def _combine_variant_signals(
    signals_by_component: dict[str, pd.DataFrame],
    variant: StrategyVariant,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for component in variant.required_components:
        component_frame = signals_by_component[component].copy()
        _require_columns(component_frame, ["signal_id", "symbol", "known_at"], scope=component)
        component_frame["component"] = component
        component_frame["component_signal_id"] = component_frame["signal_id"].astype(str)
        component_frame["signal_id"] = (
            variant.name + ":" + component + ":" + component_frame["signal_id"].astype(str)
        )
        if "source" not in component_frame.columns:
            component_frame["source"] = component
        frames.append(component_frame)
    return pd.concat(frames, ignore_index=True)


def _summary_row_from_backtest(
    variant: StrategyVariant,
    result_summary: pd.DataFrame,
    data_start: str,
    data_end: str,
    trading_cost_bps: float,
    slippage_bps: float,
    rss_context: RssContextVariantStatus | None = None,
) -> dict[str, object]:
    base = _summary_base(
        variant=variant,
        status="ok" if not result_summary.empty else "no_trades",
        missing_components=(),
        data_start=data_start,
        data_end=data_end,
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
        rss_context=rss_context,
    )
    if result_summary.empty:
        return base
    for column in VARIANT_BACKTEST_SUMMARY_COLUMNS:
        base[column] = result_summary.iloc[0].get(column, pd.NA)
    return base


def _unavailable_summary_row(
    variant: StrategyVariant,
    missing_components: tuple[str, ...],
    data_start: str,
    data_end: str,
    trading_cost_bps: float,
    slippage_bps: float,
    rss_context: RssContextVariantStatus | None = None,
) -> dict[str, object]:
    return _summary_base(
        variant=variant,
        status="unavailable",
        missing_components=missing_components,
        data_start=data_start,
        data_end=data_end,
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
        rss_context=rss_context,
    )


def _error_summary_row(
    variant: StrategyVariant,
    message: str,
    data_start: str,
    data_end: str,
    trading_cost_bps: float,
    slippage_bps: float,
    rss_context: RssContextVariantStatus | None = None,
) -> dict[str, object]:
    row = _summary_base(
        variant=variant,
        status="error",
        missing_components=(),
        data_start=data_start,
        data_end=data_end,
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
        rss_context=rss_context,
    )
    row["missing_components"] = message
    return row


def _summary_base(
    variant: StrategyVariant,
    status: str,
    missing_components: tuple[str, ...],
    data_start: str,
    data_end: str,
    trading_cost_bps: float,
    slippage_bps: float,
    rss_context: RssContextVariantStatus | None = None,
) -> dict[str, object]:
    row = {
        "variant": variant.name,
        "description": variant.description,
        "status": status,
        "components": "+".join(variant.required_components),
        "missing_components": "+".join(missing_components),
        "data_start": data_start,
        "data_end": data_end,
        "trading_cost_bps": float(trading_cost_bps),
        "slippage_bps": float(slippage_bps),
        "rss_context_status": pd.NA,
        "rss_context_evidence_count": pd.NA,
        "rss_context_source_count": pd.NA,
        "rss_context_latest_timestamp": pd.NA,
        "rss_context_warnings": pd.NA,
        "rss_context_evidence_urls": pd.NA,
    }
    if rss_context is not None:
        row.update(_rss_context_summary_fields(rss_context))
    for column in VARIANT_BACKTEST_SUMMARY_COLUMNS:
        row[column] = pd.NA
    return row


def summarize_rss_context_for_variant_e(
    rss_context: pd.DataFrame | str | Path | None,
    decision_timestamp: str | None = None,
) -> RssContextVariantStatus:
    """Summarize RSS context availability for Strategy Variant E."""

    if rss_context is None:
        report = QualityReport(
            (
                QualityIssue(
                    severity=WARNING,
                    code="MISSING_RSS_CONTEXT",
                    message="RSS context was not provided for Variant E",
                ),
            )
        )
        return RssContextVariantStatus(
            status="unavailable",
            evidence_count=0,
            source_count=0,
            latest_timestamp=None,
            evidence_urls=(),
            warnings=("MISSING_RSS_CONTEXT",),
            quality_report=report,
            evidence_bundle=None,
        )

    frame = _load_rss_context_frame(rss_context)
    missing_columns = [
        column
        for column in (
            "entity_type",
            "entity_id",
            "news_count",
            "source_count",
            "latest_news_timestamp",
            "evidence_urls",
            "decision_timestamp",
        )
        if column not in frame.columns
    ]
    if missing_columns:
        report = QualityReport(
            (
                QualityIssue(
                    severity=BLOCKING,
                    code="RSS_CONTEXT_SCHEMA_ERROR",
                    message=f"RSS context missing columns: {', '.join(missing_columns)}",
                ),
            )
        )
        return RssContextVariantStatus(
            status="warning",
            evidence_count=0,
            source_count=0,
            latest_timestamp=None,
            evidence_urls=(),
            warnings=("RSS_CONTEXT_SCHEMA_ERROR",),
            quality_report=report,
            evidence_bundle=None,
        )

    active = frame[pd.to_numeric(frame["news_count"], errors="coerce").fillna(0) > 0].copy()
    if active.empty:
        report = QualityReport(
            (
                QualityIssue(
                    severity=WARNING,
                    code="EMPTY_RSS_CONTEXT",
                    message="RSS context has no active evidence rows",
                ),
            )
        )
        return RssContextVariantStatus(
            status="unavailable",
            evidence_count=0,
            source_count=0,
            latest_timestamp=None,
            evidence_urls=(),
            warnings=("EMPTY_RSS_CONTEXT",),
            quality_report=report,
            evidence_bundle=None,
        )

    issues = _rss_context_issues(active, decision_timestamp)
    safe_active = _safe_rss_context_rows(active, decision_timestamp)
    evidence_urls = _collect_evidence_urls(safe_active)
    warnings = tuple(issue.code for issue in issues)
    latest = _latest_timestamp(safe_active)
    evidence_count = int(pd.to_numeric(safe_active["news_count"], errors="coerce").fillna(0).sum())
    source_count = int(pd.to_numeric(safe_active["source_count"], errors="coerce").fillna(0).sum())
    bundle = _build_rss_context_evidence_bundle(safe_active) if not safe_active.empty else None
    status = "available" if evidence_count > 0 else "unavailable"
    if warnings:
        status = "warning" if evidence_count > 0 else "unavailable"
    return RssContextVariantStatus(
        status=status,
        evidence_count=evidence_count,
        source_count=source_count,
        latest_timestamp=latest,
        evidence_urls=evidence_urls,
        warnings=warnings,
        quality_report=QualityReport(tuple(issues)),
        evidence_bundle=bundle,
    )


def _load_rss_context_frame(rss_context: pd.DataFrame | str | Path) -> pd.DataFrame:
    if isinstance(rss_context, pd.DataFrame):
        return rss_context.copy()
    return pd.read_csv(rss_context)


def _rss_context_issues(
    active: pd.DataFrame,
    decision_timestamp: str | None,
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    if active["latest_news_timestamp"].isna().any() or (active["latest_news_timestamp"].astype(str).str.strip() == "").any():
        issues.append(
            QualityIssue(
                severity=WARNING,
                code="RSS_CONTEXT_MISSING_TIMESTAMP",
                message="one or more RSS context rows have no latest_news_timestamp",
            )
        )
    if active["evidence_urls"].isna().any() or (active["evidence_urls"].astype(str).str.strip() == "").any():
        issues.append(
            QualityIssue(
                severity=WARNING,
                code="RSS_CONTEXT_MISSING_EVIDENCE_URLS",
                message="one or more RSS context rows have no evidence URLs",
            )
        )
    decision = decision_timestamp or _first_non_empty(active["decision_timestamp"])
    if decision:
        decision_time = pd.to_datetime(decision, utc=True, errors="coerce")
        latest = pd.to_datetime(active["latest_news_timestamp"], utc=True, errors="coerce")
        if latest.isna().any():
            issues.append(
                QualityIssue(
                    severity=WARNING,
                    code="RSS_CONTEXT_INVALID_TIMESTAMP",
                    message="one or more RSS context timestamps could not be parsed",
                )
            )
        if latest.notna().any() and (latest > decision_time).any():
            issues.append(
                QualityIssue(
                    severity=BLOCKING,
                    code="RSS_CONTEXT_FUTURE_TIMESTAMP",
                    message="RSS context includes news after the decision timestamp",
                )
            )
    return issues


def _safe_rss_context_rows(
    active: pd.DataFrame,
    decision_timestamp: str | None,
) -> pd.DataFrame:
    decision = decision_timestamp or _first_non_empty(active["decision_timestamp"])
    latest = pd.to_datetime(active["latest_news_timestamp"], utc=True, errors="coerce")
    safe = active.loc[latest.notna()].copy()
    if decision:
        decision_time = pd.to_datetime(decision, utc=True, errors="coerce")
        safe = safe.loc[latest.loc[safe.index] <= decision_time]
    return safe


def _build_rss_context_evidence_bundle(active: pd.DataFrame) -> EvidenceBundle:
    evidence = active.copy()
    evidence["source"] = "rss_context"
    evidence["source_url"] = evidence["evidence_urls"].astype(str).map(
        lambda value: value.split(";")[0] if value else ""
    )
    evidence["known_at"] = evidence["latest_news_timestamp"]
    evidence["record_id"] = (
        "rss_context:"
        + evidence["entity_type"].astype(str)
        + ":"
        + evidence["entity_id"].astype(str)
    )
    return build_evidence_bundle(
        evidence,
        feature_columns=["news_count", "source_count"],
        source_columns=["source", "source_url", "known_at", "decision_timestamp"],
    )


def _rss_context_summary_fields(status: RssContextVariantStatus) -> dict[str, object]:
    return {
        "rss_context_status": status.status,
        "rss_context_evidence_count": status.evidence_count,
        "rss_context_source_count": status.source_count,
        "rss_context_latest_timestamp": status.latest_timestamp or pd.NA,
        "rss_context_warnings": "+".join(status.warnings),
        "rss_context_evidence_urls": ";".join(status.evidence_urls[:5]),
    }


def _collect_evidence_urls(frame: pd.DataFrame) -> tuple[str, ...]:
    urls: list[str] = []
    if frame.empty:
        return ()
    for value in frame["evidence_urls"].fillna(""):
        urls.extend(url.strip() for url in str(value).split(";") if url.strip())
    return tuple(dict.fromkeys(urls))


def _latest_timestamp(frame: pd.DataFrame) -> str | None:
    if frame.empty:
        return None
    latest = pd.to_datetime(frame["latest_news_timestamp"], utc=True, errors="coerce")
    if latest.dropna().empty:
        return None
    return latest.max().isoformat()


def _first_non_empty(values: pd.Series) -> str | None:
    for value in values:
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
    return None


def _price_data_period(prices_by_symbol: dict[str, pd.DataFrame]) -> tuple[str, str]:
    dates = []
    for symbol, prices in prices_by_symbol.items():
        _require_columns(prices, ["date"], scope=symbol)
        parsed = pd.to_datetime(prices["date"], errors="raise")
        if not parsed.empty:
            dates.append(parsed)
    if not dates:
        raise StrategyVariantInputError("price data has no dates")
    combined = pd.concat(dates, ignore_index=True)
    return combined.min().date().isoformat(), combined.max().date().isoformat()


def _component_from_signal_id(signal_id: object) -> str | None:
    parts = str(signal_id).split(":", 2)
    if len(parts) < 3:
        return None
    return parts[1]


def _component_signal_id_from_signal_id(signal_id: object) -> str | None:
    parts = str(signal_id).split(":", 2)
    if len(parts) < 3:
        return None
    return parts[2]


def _require_columns(frame: pd.DataFrame, columns: list[str], scope: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise StrategyVariantInputError(f"{scope} missing required columns: {', '.join(missing)}")
