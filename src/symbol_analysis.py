"""Single-symbol classroom analysis presenter.

This module aggregates existing deterministic project artifacts into one
readable terminal/markdown output for demos. It does not create investment
advice and it does not ask an LLM to calculate market values.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.context import load_context_csv
from src.data import UniverseMember, load_universe, read_price_cache
from src.events import detect_all_events
from src.fundamentals import load_fundamentals_csv
from src.fundamentals_status import DEFAULT_FUNDAMENTALS_INPUT_PATH
from src.indicators import add_all_indicators
from src.macro_context_status import DEFAULT_MACRO_CONTEXT_INPUT_PATH
from src.research import run_technical_reversals
from src.settings import PROJECT_ROOT, Settings, load_settings


DEFAULT_SYMBOL_REPORT_DIR = PROJECT_ROOT / "reports" / "symbol_analysis"
DEFAULT_BACKTEST_REPORT_PATH = PROJECT_ROOT / "reports" / "backtest.md"
OUTPUT_LABEL_CATCH_UP = "POTENTIAL_CATCH_UP_CANDIDATE"
OUTPUT_LABEL_INVESTIGATE = "INVESTIGATE"
OUTPUT_LABEL_INCONCLUSIVE = "INCONCLUSIVE_DATA_GAP"


@dataclass(frozen=True)
class SymbolAnalysisResult:
    symbol: str
    ticker: str
    text: str
    report_path: Path
    warnings: tuple[str, ...]
    label: str


def analyze_symbol_from_settings(
    requested_symbol: str,
    settings: Settings | None = None,
    output_path: str | Path | None = None,
    fundamentals_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
    macro_context_path: str | Path = DEFAULT_MACRO_CONTEXT_INPUT_PATH,
    backtest_report_path: str | Path = DEFAULT_BACKTEST_REPORT_PATH,
) -> SymbolAnalysisResult:
    """Build and write the single-symbol demo analysis from local artifacts."""

    active_settings = settings or load_settings()
    universe = load_universe(active_settings.paths.universe)
    member = _resolve_member(requested_symbol, universe)
    warnings: list[str] = []

    prices_by_symbol = _load_prices_for_universe(
        universe=universe,
        cache_dir=active_settings.paths.cache_dir,
        warnings=warnings,
    )
    target_prices = prices_by_symbol.get(member.yahoo_symbol)
    if target_prices is None or target_prices.empty:
        text = _render_missing_symbol(member, active_settings.paths.cache_dir)
        report = _write_symbol_report(text, member.yahoo_symbol, output_path)
        return SymbolAnalysisResult(
            symbol=member.yahoo_symbol,
            ticker=member.ticker,
            text=text,
            report_path=report,
            warnings=tuple(warnings),
            label=OUTPUT_LABEL_INCONCLUSIVE,
        )

    market = _market_snapshot(target_prices)
    sector = _sector_snapshot(member, prices_by_symbol, universe)
    technical = _technical_snapshot(member.yahoo_symbol, target_prices, prices_by_symbol)
    fundamentals = _fundamentals_snapshot(member, universe, fundamentals_path, warnings)
    macro = _macro_snapshot(macro_context_path, warnings)
    backtest = _backtest_snapshot(backtest_report_path, warnings)
    data_quality = _data_quality_snapshot(
        member=member,
        prices=target_prices,
        market=market,
        sector=sector,
        technical=technical,
        fundamentals=fundamentals,
        macro=macro,
        backtest=backtest,
        warnings=warnings,
    )
    label = _analysis_label(
        data_quality=data_quality,
        sector=sector,
        technical=technical,
        fundamentals=fundamentals,
        macro=macro,
    )

    text = _render_analysis(
        member=member,
        settings=active_settings,
        market=market,
        sector=sector,
        technical=technical,
        fundamentals=fundamentals,
        macro=macro,
        backtest=backtest,
        data_quality=data_quality,
        label=label,
        warnings=warnings,
    )
    report = _write_symbol_report(text, member.yahoo_symbol, output_path)
    return SymbolAnalysisResult(
        symbol=member.yahoo_symbol,
        ticker=member.ticker,
        text=text,
        report_path=report,
        warnings=tuple(warnings),
        label=label,
    )


def _resolve_member(requested_symbol: str, universe: list[UniverseMember]) -> UniverseMember:
    normalized = requested_symbol.strip().upper()
    if normalized == "ANALYZE":
        raise ValueError("a ticker is required after Analyze")

    for member in universe:
        if normalized in {member.ticker.upper(), member.yahoo_symbol.upper()}:
            return member
    if not normalized.endswith(".IS"):
        candidate = f"{normalized}.IS"
        for member in universe:
            if candidate == member.yahoo_symbol.upper():
                return member
    raise ValueError(f"{requested_symbol} is not in the fixed 30-stock universe")


def _load_prices_for_universe(
    universe: list[UniverseMember],
    cache_dir: str | Path,
    warnings: list[str],
) -> dict[str, pd.DataFrame]:
    prices: dict[str, pd.DataFrame] = {}
    for member in universe:
        try:
            frame = read_price_cache(cache_dir, member.yahoo_symbol)
            if frame.empty:
                warnings.append(f"{member.yahoo_symbol}: empty market cache")
                continue
            prices[member.yahoo_symbol] = frame
        except Exception as exc:
            warnings.append(f"{member.yahoo_symbol}: market cache missing or unreadable ({exc})")
    return prices


def _market_snapshot(prices: pd.DataFrame) -> dict[str, object]:
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna(subset=["date", "close"]).sort_values("date")
    if frame.empty:
        return {"status": "missing"}
    return {
        "status": "pass",
        "first_date": frame["date"].iloc[0].date().isoformat(),
        "last_date": frame["date"].iloc[-1].date().isoformat(),
        "row_count": int(len(frame)),
        "latest_close": float(frame["close"].iloc[-1]),
    }


def _sector_snapshot(
    member: UniverseMember,
    prices_by_symbol: dict[str, pd.DataFrame],
    universe: list[UniverseMember],
    lookback_days: int = 20,
) -> dict[str, object]:
    try:
        returns: dict[str, float] = {}
        for current in universe:
            frame = prices_by_symbol.get(current.yahoo_symbol)
            if frame is None or len(frame) <= lookback_days:
                continue
            ordered = frame.copy()
            ordered["date"] = pd.to_datetime(ordered["date"], errors="coerce")
            ordered["close"] = pd.to_numeric(ordered["close"], errors="coerce")
            ordered = ordered.dropna(subset=["date", "close"]).sort_values("date")
            if len(ordered) <= lookback_days:
                continue
            latest_close = float(ordered["close"].iloc[-1])
            previous_close = float(ordered["close"].iloc[-lookback_days - 1])
            returns[current.yahoo_symbol] = latest_close / previous_close - 1

        target_return = returns.get(member.yahoo_symbol)
        peer_symbols = [
            current.yahoo_symbol
            for current in universe
            if current.sector == member.sector and current.yahoo_symbol != member.yahoo_symbol
        ]
        peer_returns = [returns[symbol] for symbol in peer_symbols if symbol in returns]
        if target_return is None:
            return {"status": "inconclusive", "reason": "insufficient target history"}
        if not peer_returns:
            return {
                "status": "inconclusive",
                "reason": "insufficient same-sector peers in fixed universe",
                "symbol_return": target_return,
                "peer_count": 0,
            }

        peer_median = float(pd.Series(peer_returns).median())
        lag_score = target_return - peer_median
        return {
            "status": "pass",
            "sector": member.sector,
            "lookback_days": lookback_days,
            "symbol_return": target_return,
            "peer_median_return": peer_median,
            "lag_score": lag_score,
            "peer_count": len(peer_returns),
        }
    except Exception as exc:
        return {"status": "warning", "reason": str(exc)}


def _technical_snapshot(
    symbol: str,
    prices: pd.DataFrame,
    prices_by_symbol: dict[str, pd.DataFrame],
) -> dict[str, object]:
    try:
        enriched = add_all_indicators(prices)
        latest = enriched.dropna(subset=["close"]).iloc[-1]
        prior_index = max(0, len(enriched) - 6)
        previous_kama = enriched["kama_10"].iloc[prior_index]
        current_kama = latest.get("kama_10")
        kama_state = _trend_label(current_kama, previous_kama)
        direction = latest.get("supertrend_direction")
        supertrend_state = (
            "bullish"
            if pd.notna(direction) and float(direction) > 0
            else "bearish"
            if pd.notna(direction) and float(direction) < 0
            else "unknown"
        )

        detected = detect_all_events(enriched, symbol=symbol)
        events = detected.events
        lower_band_recent = _has_recent_event(
            events,
            family="bollinger",
            event_type="lower_band_touch",
            latest_date=str(latest["date"]),
            lookback_days=20,
        )
        historical = _technical_history(symbol, prices, events, prices_by_symbol)
        return {
            "status": "pass" if not detected.errors else "warning",
            "rsi": _safe_float(latest.get("rsi_14")),
            "kama": kama_state,
            "supertrend": supertrend_state,
            "lower_bollinger_event": lower_band_recent,
            "latest_event": _latest_event_descriptor(events),
            "historical": historical,
            "event_errors": tuple(f"{e.detector}: {e.message}" for e in detected.errors),
        }
    except Exception as exc:
        return {"status": "warning", "reason": str(exc), "historical": _empty_history()}


def _technical_history(
    symbol: str,
    prices: pd.DataFrame,
    events: pd.DataFrame,
    prices_by_symbol: dict[str, pd.DataFrame],
) -> dict[str, object]:
    if events.empty:
        return _empty_history("no detected technical events")
    latest_event = events.sort_values("event_date").iloc[-1]
    try:
        result = run_technical_reversals(
            prices_by_symbol={symbol: prices},
            events_by_symbol={symbol: events},
            benchmark_prices=None,
            horizons=(5,),
            regime_lookback_days=20,
        )
        observations = result.observations
        if observations.empty:
            return _empty_history("no eligible 5D technical observations")
        similar = observations[
            (observations["status"] == "ok")
            & (pd.to_numeric(observations["horizon"], errors="coerce") == 5)
            & (observations["event_family"].astype(str) == str(latest_event["event_family"]))
            & (observations["event_type"].astype(str) == str(latest_event["event_type"]))
        ].copy()
        if similar.empty:
            similar = observations[
                (observations["status"] == "ok")
                & (pd.to_numeric(observations["horizon"], errors="coerce") == 5)
            ].copy()
        returns = pd.to_numeric(similar["forward_return"], errors="coerce").dropna()
        return {
            "status": "pass" if len(returns) else "inconclusive",
            "similar_events": int(len(returns)),
            "positive_after_5d": int((returns > 0).sum()),
            "median_5d_return": float(returns.median()) if len(returns) else None,
            "event_family": str(latest_event["event_family"]),
            "event_type": str(latest_event["event_type"]),
        }
    except Exception as exc:
        return _empty_history(str(exc))


def _fundamentals_snapshot(
    member: UniverseMember,
    universe: list[UniverseMember],
    fundamentals_path: str | Path,
    warnings: list[str],
) -> dict[str, object]:
    try:
        imported = load_fundamentals_csv(fundamentals_path, universe)
        warnings.extend(f"fundamentals row {e.row_number or 'file'}: {e.message}" for e in imported.errors)
        records = imported.records[imported.records["yahoo_symbol"] == member.yahoo_symbol].copy()
        if records.empty:
            return {"status": "inconclusive", "reason": "no fundamentals rows for symbol"}
        records["period_end_dt"] = pd.to_datetime(records["period_end"], errors="coerce")
        records = records.dropna(subset=["period_end_dt"]).sort_values("period_end_dt")
        latest = records.iloc[-1]
        previous = records.iloc[-2] if len(records) >= 2 else None
        previous_year = records.iloc[-5] if len(records) >= 5 else None

        primary_metric = "net_interest_income" if str(latest["metric_profile"]) == "bank" else "revenue"
        yoy_change = _relative_change(latest.get(primary_metric), previous_year.get(primary_metric) if previous_year is not None else None)
        qoq_change = _relative_change(latest.get(primary_metric), previous.get(primary_metric) if previous is not None else None)
        current_margin = _operating_margin(latest)
        previous_margin = _operating_margin(previous) if previous is not None else None
        margin_change = (
            current_margin - previous_margin
            if current_margin is not None and previous_margin is not None
            else None
        )
        return {
            "status": "pass",
            "metric_profile": str(latest["metric_profile"]),
            "primary_metric": primary_metric,
            "period_end": str(latest["period_end"]),
            "disclosure_timestamp": str(latest["disclosure_timestamp"]),
            "primary_yoy": yoy_change,
            "primary_qoq": qoq_change,
            "operating_margin": current_margin,
            "operating_margin_change": margin_change,
        }
    except Exception as exc:
        return {"status": "warning", "reason": str(exc)}


def _macro_snapshot(path: str | Path, warnings: list[str]) -> dict[str, object]:
    try:
        imported = load_context_csv(path)
        warnings.extend(f"macro row {e.row_number or 'file'}: {e.message}" for e in imported.errors)
        records = imported.records
        if records.empty:
            return {"status": "inconclusive", "reason": "no macro context rows"}
        macro = records[records["context_type"] == "macro"].copy()
        if macro.empty:
            return {"status": "inconclusive", "reason": "no macro rows"}
        macro["publication_dt"] = pd.to_datetime(macro["publication_timestamp"], errors="coerce", utc=True)
        latest_by_indicator = {}
        for indicator, group in macro.dropna(subset=["publication_dt"]).groupby("indicator"):
            latest = group.sort_values("publication_dt").iloc[-1]
            latest_by_indicator[str(indicator)] = {
                "value": _safe_float(latest.get("value")),
                "unit": str(latest.get("unit") or ""),
                "source": str(latest.get("source") or ""),
            }
        hard_risk = _macro_hard_risk(latest_by_indicator)
        return {
            "status": "pass",
            "latest": latest_by_indicator,
            "hard_risk": hard_risk,
        }
    except Exception as exc:
        return {"status": "warning", "reason": str(exc), "hard_risk": False}


def _backtest_snapshot(path: str | Path, warnings: list[str]) -> dict[str, object]:
    try:
        text = Path(path).read_text(encoding="utf-8")
        summary = _parse_markdown_summary_row(text)
        if not summary:
            return {"status": "inconclusive", "reason": "summary table not found"}
        sanity_warnings = _backtest_sanity_warnings(summary)
        return {
            "status": "warning" if sanity_warnings else "pass",
            "sanity_warnings": tuple(sanity_warnings),
            **summary,
        }
    except Exception as exc:
        warnings.append(f"backtest report unavailable: {exc}")
        return {"status": "warning", "reason": str(exc)}


def _parse_markdown_summary_row(text: str) -> dict[str, object]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "## Summary":
            for candidate in lines[index + 1 : index + 12]:
                cells = [cell.strip() for cell in candidate.strip().strip("|").split("|")]
                if cells and cells[0] == "ok" and len(cells) >= 14:
                    return {
                        "signal_count": _parse_number(cells[1]),
                        "trade_count": _parse_number(cells[2]),
                        "cumulative_return": _parse_number(cells[8]),
                        "sharpe_ratio": _parse_number(cells[9]),
                        "maximum_drawdown": _parse_number(cells[10]),
                        "win_rate": _parse_number(cells[11]),
                        "benchmark_difference": _parse_number(cells[13]),
                    }
    return {}


def _backtest_sanity_warnings(summary: dict[str, object]) -> list[str]:
    warnings: list[str] = []
    required = ("cumulative_return", "sharpe_ratio", "maximum_drawdown", "benchmark_difference")
    for key in required:
        if summary.get(key) is None:
            warnings.append(f"backtest missing {key}")

    cumulative = _safe_float(summary.get("cumulative_return"))
    benchmark_difference = _safe_float(summary.get("benchmark_difference"))
    sharpe = _safe_float(summary.get("sharpe_ratio"))
    drawdown = _safe_float(summary.get("maximum_drawdown"))

    if cumulative is not None and abs(cumulative) > 10:
        warnings.append("unrealistic cumulative_return magnitude; rerun measured backtests")
    if benchmark_difference is not None and abs(benchmark_difference) > 10:
        warnings.append("unrealistic benchmark_difference magnitude; rerun measured backtests")
    if sharpe is not None and abs(sharpe) > 10:
        warnings.append("unusually large sharpe_ratio; inspect risk metric assumptions")
    if drawdown is not None and (drawdown < -1 or drawdown > 0):
        warnings.append("maximum_drawdown is outside expected [-1, 0] range")
    return warnings


def _data_quality_snapshot(
    member: UniverseMember,
    prices: pd.DataFrame,
    market: dict[str, object],
    sector: dict[str, object],
    technical: dict[str, object],
    fundamentals: dict[str, object],
    macro: dict[str, object],
    backtest: dict[str, object],
    warnings: list[str],
) -> dict[str, object]:
    blocking = []
    quality_warnings: list[str] = []
    if market.get("status") != "pass":
        blocking.append("market data missing")
    if prices.empty:
        blocking.append("empty price history")
    if backtest.get("status") != "pass":
        quality_warnings.append(f"backtest status is {backtest.get('status', 'unknown')}")
    quality_warnings.extend(str(item) for item in backtest.get("sanity_warnings", ()))
    if macro.get("hard_risk"):
        quality_warnings.append("macro hard-risk flag is active")
    non_blocking = [
        name
        for name, snapshot in (
            ("sector", sector),
            ("technical", technical),
            ("fundamentals", fundamentals),
            ("macro", macro),
            ("backtest", backtest),
        )
        if snapshot.get("status") not in {"pass", "PASS"}
    ]
    if blocking:
        status = "FAIL"
    elif any("unrealistic" in warning or "missing" in warning for warning in quality_warnings):
        status = "INVESTIGATE"
    elif quality_warnings or non_blocking:
        status = "PASS_WITH_WARNINGS"
    else:
        status = "PASS"
    return {
        "status": status,
        "blocking": tuple(blocking),
        "non_blocking": tuple(non_blocking),
        "quality_warnings": tuple(quality_warnings),
        "warning_count": len(warnings) + len(quality_warnings),
        "symbol": member.yahoo_symbol,
    }


def _analysis_label(
    data_quality: dict[str, object],
    sector: dict[str, object],
    technical: dict[str, object],
    fundamentals: dict[str, object],
    macro: dict[str, object],
) -> str:
    if data_quality.get("status") != "PASS":
        if data_quality.get("status") in {"PASS_WITH_WARNINGS", "INVESTIGATE"}:
            return OUTPUT_LABEL_INVESTIGATE
        return OUTPUT_LABEL_INCONCLUSIVE
    if macro.get("hard_risk"):
        return OUTPUT_LABEL_INVESTIGATE

    lag_score = sector.get("lag_score")
    historical = technical.get("historical", {})
    historical_median = historical.get("median_5d_return")
    constructive_technical = (
        technical.get("supertrend") == "bullish"
        or (technical.get("rsi") is not None and float(technical["rsi"]) < 45)
        or bool(technical.get("lower_bollinger_event"))
    )
    improving_fundamentals = any(
        value is not None and value > 0
        for value in (
            fundamentals.get("primary_yoy"),
            fundamentals.get("primary_qoq"),
            fundamentals.get("operating_margin_change"),
        )
    )
    if (
        lag_score is not None
        and float(lag_score) < 0
        and constructive_technical
        and historical_median is not None
        and float(historical_median) > 0
    ):
        return OUTPUT_LABEL_CATCH_UP
    if improving_fundamentals and constructive_technical:
        return OUTPUT_LABEL_CATCH_UP
    return OUTPUT_LABEL_INVESTIGATE


def _ai_analysis_paragraph(
    member: UniverseMember,
    sector: dict[str, object],
    technical: dict[str, object],
    fundamentals: dict[str, object],
    macro: dict[str, object],
    backtest: dict[str, object],
    data_quality: dict[str, object],
    label: str,
) -> str:
    historical = technical.get("historical", {})
    sector_clause = (
        f"{member.ticker} is lagging its same-sector peer set by {_fmt_pct(sector.get('lag_score'))}"
        if sector.get("lag_score") is not None
        else "same-sector catch-up evidence is inconclusive because peer coverage is limited"
    )
    technical_clause = (
        f"the latest technical context shows RSI {_fmt_number(technical.get('rsi'))}, "
        f"{technical.get('supertrend', 'unknown')} Supertrend, and "
        f"{historical.get('similar_events', 0)} comparable events with median 5D return "
        f"{_fmt_pct(historical.get('median_5d_return'))}"
    )
    fundamentals_clause = (
        f"fundamentals show {fundamentals.get('primary_metric', 'primary metric')} YoY "
        f"{_trend_from_value(fundamentals.get('primary_yoy'))} and operating margin change "
        f"{_trend_from_value(fundamentals.get('operating_margin_change'))}"
    )
    macro_clause = (
        "macro context has no hard-risk flag"
        if not macro.get("hard_risk")
        else "macro context has an active hard-risk flag"
    )
    backtest_clause = (
        f"the measured backtest contributes {_fmt_int(backtest.get('trade_count'))} tradable rows, "
        f"Sharpe {_fmt_number(backtest.get('sharpe_ratio'))}, max drawdown "
        f"{_fmt_pct(backtest.get('maximum_drawdown'))}, and benchmark difference "
        f"{_fmt_pct(backtest.get('benchmark_difference'))}"
        if backtest.get("status") == "pass"
        else f"backtest evidence is {backtest.get('status', 'inconclusive')}"
    )
    gate_clause = f"Data quality gate result is {data_quality.get('status', 'UNKNOWN')}."
    return (
        f"{label}: {sector_clause}; {technical_clause}. {fundamentals_clause}. "
        f"{macro_clause}, while {backtest_clause}. {gate_clause} The label is therefore an "
        "educational investigation signal tied to the cited evidence files, not a buy/sell instruction."
    )


def _render_analysis(
    member: UniverseMember,
    settings: Settings,
    market: dict[str, object],
    sector: dict[str, object],
    technical: dict[str, object],
    fundamentals: dict[str, object],
    macro: dict[str, object],
    backtest: dict[str, object],
    data_quality: dict[str, object],
    label: str,
    warnings: list[str],
) -> str:
    historical = technical.get("historical", {})
    latest_macro = macro.get("latest", {})
    ai_paragraph = _ai_analysis_paragraph(
        member=member,
        sector=sector,
        technical=technical,
        fundamentals=fundamentals,
        macro=macro,
        backtest=backtest,
        data_quality=data_quality,
        label=label,
    )
    lines = [
        f"Analyze {member.yahoo_symbol}",
        "",
        "MARKET DATA",
        f"{market.get('first_date', 'n/a')} - {market.get('last_date', 'n/a')} loaded successfully.",
        f"Rows: {market.get('row_count', 0)}",
        f"Latest close: {_fmt_number(market.get('latest_close'))}",
        "Source: data/cache/<symbol>.csv via local yfinance market cache.",
        "",
        "SECTOR ANALYSIS",
        f"Sector: {member.sector}",
        f"{member.ticker} {sector.get('lookback_days', 20)}D return: {_fmt_pct(sector.get('symbol_return'))}",
        f"Sector median: {_fmt_pct(sector.get('peer_median_return'))}",
        f"Lag score: {_fmt_pct(sector.get('lag_score'))}",
        f"Peer count: {sector.get('peer_count', 0)}",
        f"Status: {sector.get('status', 'unknown')}",
        "Source: local price cache and config/universe.csv same-sector peers.",
        "",
        "TECHNICAL",
        f"RSI: {_fmt_number(technical.get('rsi'))}",
        f"KAMA: {technical.get('kama', 'unknown')}",
        f"Supertrend: {technical.get('supertrend', 'unknown')}",
        f"Lower Bollinger event detected: {_yes_no(technical.get('lower_bollinger_event'))}",
        f"Latest event: {technical.get('latest_event', 'n/a')}",
        "Source: src/indicators.py and src/events.py deterministic calculations.",
        "",
        "HISTORICAL TEST",
        f"Similar events: {historical.get('similar_events', 0)}",
        f"Positive after 5 days: {historical.get('positive_after_5d', 0)}",
        f"Median 5D return: {_fmt_pct(historical.get('median_5d_return'))}",
        f"Event group: {historical.get('event_family', 'n/a')} / {historical.get('event_type', 'n/a')}",
        "Source: technical reversal replay from local event history.",
        "",
        "FUNDAMENTALS",
        f"Metric profile: {fundamentals.get('metric_profile', 'n/a')}",
        f"Latest period: {fundamentals.get('period_end', 'n/a')}",
        f"Primary metric ({fundamentals.get('primary_metric', 'n/a')}) YoY: {_trend_from_value(fundamentals.get('primary_yoy'))}",
        f"Primary metric QoQ: {_trend_from_value(fundamentals.get('primary_qoq'))}",
        f"Operating margin: {_fmt_pct(fundamentals.get('operating_margin'))}",
        f"Operating margin change: {_trend_from_value(fundamentals.get('operating_margin_change'))}",
        "Source: data/fundamentals/fundamentals.csv with synthetic disclosure timestamps.",
        "",
        "MACRO",
        f"Hard-risk flag: {_yes_no(macro.get('hard_risk'))}",
        f"USD/TRY: {_macro_value(latest_macro, 'usd_try')}",
        f"EUR/TRY: {_macro_value(latest_macro, 'eur_try')}",
        f"TCMB policy rate: {_macro_value(latest_macro, 'tcmb_policy_rate')}",
        f"TUIK inflation: {_macro_value(latest_macro, 'tuik_inflation')}",
        f"FED policy rate: {_macro_value(latest_macro, 'fed_policy_rate')}",
        "Source: data/macro/macro_context.csv and reports/macro_context_status.md.",
        "",
        "BACKTEST",
        f"Signal count: {_fmt_int(backtest.get('signal_count'))}",
        f"Trade count: {_fmt_int(backtest.get('trade_count'))}",
        f"Cumulative return: {_fmt_pct(backtest.get('cumulative_return'))}",
        f"Sharpe: {_fmt_number(backtest.get('sharpe_ratio'))}",
        f"Max drawdown: {_fmt_pct(backtest.get('maximum_drawdown'))}",
        f"Benchmark difference: {_fmt_pct(backtest.get('benchmark_difference'))}",
        "Source: reports/backtest.md.",
        "",
        "DATA QUALITY",
        str(data_quality.get("status", "UNKNOWN")),
        f"Warnings: {data_quality.get('warning_count', 0)}",
        "",
        "AI ANALYSIS",
        label,
        ai_paragraph,
        "",
        "Evidence:",
        "E1 reports/research_run_status.md - measured scenario report status.",
        "E2 reports/backtest.md - cost-adjusted backtest and risk summary.",
        "E3 reports/strategy_variants.md - A-E strategy comparison and unavailable component notes.",
        "E4 reports/llm_agent_harness.md - constrained LLM explanation/replay status.",
        "E5 reports/pdf_requirement_coverage.md - PDF requirement coverage and limitations.",
        "",
        "Warning:",
        "Historical evidence does not guarantee future returns. This is educational research output, not investment advice.",
    ]
    quality_warnings = data_quality.get("quality_warnings", ())
    if quality_warnings:
        lines.extend(["", "Quality Gate Notes:"])
        lines.extend(f"- {warning}" for warning in quality_warnings)
    if warnings:
        lines.extend(["", "Runtime Warnings:"])
        lines.extend(f"- {warning}" for warning in warnings[:10])
        if len(warnings) > 10:
            lines.append(f"- ... {len(warnings) - 10} more warnings")
    lines.extend(
        [
            "",
            "Run context:",
            f"Cache dir: {settings.paths.cache_dir}",
            f"Report generated from local artifacts under: {settings.paths.reports_dir}",
        ]
    )
    return "\n".join(lines)


def _render_missing_symbol(member: UniverseMember, cache_dir: Path) -> str:
    return "\n".join(
        [
            f"Analyze {member.yahoo_symbol}",
            "",
            "DATA QUALITY",
            "FAIL",
            f"Missing local market cache for {member.yahoo_symbol} under {cache_dir}.",
            "",
            "AI ANALYSIS",
            OUTPUT_LABEL_INCONCLUSIVE,
            "",
            "Warning:",
            "No market-data-backed analysis was produced.",
        ]
    )


def _write_symbol_report(text: str, symbol: str, output_path: str | Path | None) -> Path:
    path = Path(output_path) if output_path is not None else DEFAULT_SYMBOL_REPORT_DIR / f"{_safe_symbol(symbol)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _safe_symbol(symbol: str) -> str:
    return symbol.replace(".", "_").replace("/", "_")


def _empty_history(reason: str | None = None) -> dict[str, object]:
    return {
        "status": "inconclusive",
        "similar_events": 0,
        "positive_after_5d": 0,
        "median_5d_return": None,
        "event_family": "n/a",
        "event_type": reason or "n/a",
    }


def _latest_event_descriptor(events: pd.DataFrame) -> str:
    if events.empty:
        return "none"
    latest = events.sort_values("event_date").iloc[-1]
    return f"{latest['event_family']}/{latest['event_type']} on {latest['event_date']}"


def _has_recent_event(
    events: pd.DataFrame,
    family: str,
    event_type: str,
    latest_date: str,
    lookback_days: int,
) -> bool:
    if events.empty:
        return False
    frame = events.copy()
    frame["event_dt"] = pd.to_datetime(frame["event_date"], errors="coerce")
    latest_dt = pd.to_datetime(latest_date, errors="coerce")
    if pd.isna(latest_dt):
        return False
    cutoff = latest_dt - pd.Timedelta(days=lookback_days)
    mask = (
        (frame["event_family"].astype(str) == family)
        & (frame["event_type"].astype(str) == event_type)
        & (frame["event_dt"] >= cutoff)
        & (frame["event_dt"] <= latest_dt)
    )
    return bool(mask.any())


def _relative_change(current: object, previous: object) -> float | None:
    current_number = _safe_float(current)
    previous_number = _safe_float(previous)
    if current_number is None or previous_number in {None, 0.0}:
        return None
    return current_number / previous_number - 1


def _operating_margin(row: pd.Series | None) -> float | None:
    if row is None:
        return None
    operating_profit = _safe_float(row.get("operating_profit"))
    revenue = _safe_float(row.get("revenue"))
    if operating_profit is None or revenue in {None, 0.0}:
        return None
    return operating_profit / revenue


def _trend_label(current: object, previous: object) -> str:
    current_number = _safe_float(current)
    previous_number = _safe_float(previous)
    if current_number is None or previous_number is None:
        return "unknown"
    if current_number > previous_number:
        return "improving"
    if current_number < previous_number:
        return "weakening"
    return "flat"


def _macro_hard_risk(latest: dict[str, dict[str, object]]) -> bool:
    inflation = latest.get("tuik_inflation", {}).get("value")
    policy_rate = latest.get("tcmb_policy_rate", {}).get("value")
    try:
        return bool(
            (inflation is not None and float(inflation) >= 80)
            or (policy_rate is not None and float(policy_rate) >= 60)
        )
    except Exception:
        return False


def _macro_value(latest: dict[str, dict[str, object]], indicator: str) -> str:
    row = latest.get(indicator)
    if not row:
        return "n/a"
    value = _fmt_number(row.get("value"))
    unit = row.get("unit") or ""
    return f"{value} {unit}".strip()


def _parse_number(value: str) -> float | int | None:
    cleaned = value.strip()
    if cleaned.lower() in {"", "nan", "none", "n/a"}:
        return None
    try:
        number = float(cleaned)
    except Exception:
        return None
    return int(number) if number.is_integer() else number


def _safe_float(value: object) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        number = float(value)
    except Exception:
        return None
    return number


def _fmt_pct(value: object) -> str:
    number = _safe_float(value)
    if number is None:
        return "n/a"
    percent = number * 100
    if abs(percent) >= 100000:
        return f"{percent:+.2e}%"
    return f"{percent:+.2f}%"


def _fmt_number(value: object) -> str:
    number = _safe_float(value)
    if number is None:
        return "n/a"
    if abs(number) >= 1000:
        return f"{number:,.2f}"
    return f"{number:.2f}"


def _fmt_int(value: object) -> str:
    number = _safe_float(value)
    if number is None:
        return "n/a"
    return f"{int(number):,}"


def _yes_no(value: object) -> str:
    return "yes" if bool(value) else "no"


def _trend_from_value(value: object) -> str:
    number = _safe_float(value)
    if number is None:
        return "n/a"
    direction = "improving" if number > 0 else "weakening" if number < 0 else "flat"
    return f"{direction} ({_fmt_pct(number)})"


def command_symbol_from_args(args: list[str]) -> str:
    """Accept either `ASELS.IS` or classroom-style `Analyze ASELS.IS`."""

    cleaned = [arg for arg in args if arg.strip()]
    if not cleaned:
        raise ValueError("usage: python -m scripts.analyze_symbol ASELS.IS")
    if cleaned[0].lower() == "analyze":
        cleaned = cleaned[1:]
    if not cleaned:
        raise ValueError("usage: python -m scripts.analyze_symbol Analyze ASELS.IS")
    return cleaned[0]


def strip_ansi(text: str) -> str:
    """Small helper for tests and transcript export."""

    return re.sub(r"\x1b\[[0-9;]*m", "", text)
