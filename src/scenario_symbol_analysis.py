"""Per-symbol scenario analysis commands for the four required PDF experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data import UniverseMember, load_universe, read_price_cache
from src.events import detect_all_events
from src.fundamentals import load_fundamentals_csv
from src.fundamentals_status import DEFAULT_FUNDAMENTALS_INPUT_PATH
from src.indicators import add_all_indicators
from src.research import (
    run_quarterly_fundamentals,
    run_sector_catch_up,
    run_technical_reversals,
    run_weekday_patterns,
)
from src.settings import PROJECT_ROOT, Settings, load_settings


DEFAULT_SCENARIO_REPORT_DIR = PROJECT_ROOT / "reports" / "scenario_analysis"


@dataclass(frozen=True)
class ScenarioAnalysisResult:
    scenario: str
    symbol: str
    ticker: str
    text: str
    report_path: Path
    warnings: tuple[str, ...]


def analyze_sector_catchup_from_settings(
    requested_symbol: str,
    settings: Settings | None = None,
    output_path: str | Path | None = None,
) -> ScenarioAnalysisResult:
    active_settings = settings or load_settings()
    universe = load_universe(active_settings.paths.universe)
    member = _resolve_member(requested_symbol, universe)
    warnings: list[str] = []
    prices = _load_prices(universe, active_settings.paths.cache_dir, warnings)
    result = run_sector_catch_up(prices, universe, lookback_days=20, horizons=(5, 10, 20))
    warnings.extend(f"{error.scope}: {error.message}" for error in result.errors)
    symbol_rows = result.observations[result.observations["symbol"] == member.yahoo_symbol].copy()
    text = _render_sector_catchup(member, symbol_rows, warnings)
    report = _write_report(text, output_path, "sector_catchup", member.yahoo_symbol)
    return ScenarioAnalysisResult("sector_catchup", member.yahoo_symbol, member.ticker, text, report, tuple(warnings))


def analyze_weekday_pattern_from_settings(
    requested_symbol: str,
    settings: Settings | None = None,
    output_path: str | Path | None = None,
) -> ScenarioAnalysisResult:
    active_settings = settings or load_settings()
    universe = load_universe(active_settings.paths.universe)
    member = _resolve_member(requested_symbol, universe)
    warnings: list[str] = []
    prices = _load_single_price(member, active_settings.paths.cache_dir, warnings)
    benchmark = _load_optional_price(active_settings.market_data.benchmark_symbol, active_settings.paths.cache_dir, warnings)
    result = run_weekday_patterns(
        prices_by_symbol={member.yahoo_symbol: prices} if prices is not None else {},
        benchmark_prices=benchmark,
        holding_days=(1, 2, 3, 4, 5),
        trading_cost_bps=active_settings.backtest.trading_cost_bps,
        slippage_bps=active_settings.backtest.slippage_bps,
        regime_lookback_days=active_settings.experiment.regime_lookback_days,
        unseen_start_date=active_settings.experiment.unseen_start_date,
    )
    warnings.extend(f"{error.scope}: {error.message}" for error in result.errors)
    text = _render_weekday_pattern(member, result.observations, warnings)
    report = _write_report(text, output_path, "weekday_pattern", member.yahoo_symbol)
    return ScenarioAnalysisResult("weekday_pattern", member.yahoo_symbol, member.ticker, text, report, tuple(warnings))


def analyze_technical_reversal_from_settings(
    requested_symbol: str,
    settings: Settings | None = None,
    output_path: str | Path | None = None,
) -> ScenarioAnalysisResult:
    active_settings = settings or load_settings()
    universe = load_universe(active_settings.paths.universe)
    member = _resolve_member(requested_symbol, universe)
    warnings: list[str] = []
    prices = _load_single_price(member, active_settings.paths.cache_dir, warnings)
    benchmark = _load_optional_price(active_settings.market_data.benchmark_symbol, active_settings.paths.cache_dir, warnings)
    if prices is None:
        observations = pd.DataFrame()
        events = pd.DataFrame()
        enriched = pd.DataFrame()
    else:
        enriched = add_all_indicators(prices)
        detected = detect_all_events(enriched, symbol=member.yahoo_symbol)
        events = detected.events
        warnings.extend(f"{error.detector}: {error.message}" for error in detected.errors)
        result = run_technical_reversals(
            prices_by_symbol={member.yahoo_symbol: prices},
            events_by_symbol={member.yahoo_symbol: events},
            benchmark_prices=benchmark,
            horizons=(1, 3, 5, 10),
            regime_lookback_days=active_settings.experiment.regime_lookback_days,
        )
        observations = result.observations
        warnings.extend(f"{error.scope}: {error.message}" for error in result.errors)
    text = _render_technical_reversal(member, enriched, events, observations, warnings)
    report = _write_report(text, output_path, "technical_reversal", member.yahoo_symbol)
    return ScenarioAnalysisResult("technical_reversal", member.yahoo_symbol, member.ticker, text, report, tuple(warnings))


def analyze_fundamentals_reaction_from_settings(
    requested_symbol: str,
    settings: Settings | None = None,
    output_path: str | Path | None = None,
    fundamentals_path: str | Path = DEFAULT_FUNDAMENTALS_INPUT_PATH,
) -> ScenarioAnalysisResult:
    active_settings = settings or load_settings()
    universe = load_universe(active_settings.paths.universe)
    member = _resolve_member(requested_symbol, universe)
    warnings: list[str] = []
    prices = _load_prices(universe, active_settings.paths.cache_dir, warnings)
    benchmark = _load_optional_price(active_settings.market_data.benchmark_symbol, active_settings.paths.cache_dir, warnings)
    imported = load_fundamentals_csv(fundamentals_path, universe)
    warnings.extend(f"fundamentals row {error.row_number or 'file'}: {error.message}" for error in imported.errors)
    result = run_quarterly_fundamentals(
        fundamentals=imported.records,
        prices_by_symbol=prices,
        benchmark_prices=benchmark,
        horizons=(1, 5, 20),
    )
    warnings.extend(f"{error.scope}: {error.message}" for error in result.errors)
    symbol_rows = result.observations[result.observations["symbol"] == member.yahoo_symbol].copy()
    text = _render_fundamentals_reaction(member, symbol_rows, warnings)
    report = _write_report(text, output_path, "fundamentals_reaction", member.yahoo_symbol)
    return ScenarioAnalysisResult("fundamentals_reaction", member.yahoo_symbol, member.ticker, text, report, tuple(warnings))


def _render_sector_catchup(
    member: UniverseMember,
    rows: pd.DataFrame,
    warnings: list[str],
) -> str:
    lines = [
        f"Scenario 1 - Sector Laggard / Catch-Up: {member.yahoo_symbol}",
        "",
        "LATEST SECTOR SNAPSHOT",
    ]
    if rows.empty:
        lines.append("No sector observations available.")
    else:
        latest_date = rows["date"].max()
        latest = rows[(rows["date"] == latest_date)].sort_values("horizon").iloc[0]
        lines.extend(
            [
                f"Date: {latest_date}",
                f"Sector: {member.sector}",
                f"{member.ticker} 20D return: {_fmt_pct(latest.get('lookback_return'))}",
                f"Sector peer median: {_fmt_pct(latest.get('peer_median_lookback_return'))}",
                f"Lag score: {_fmt_pct(latest.get('catch_up_score'))}",
                f"Peer count: {_fmt_int(latest.get('peer_count'))}",
                f"Laggard: {_yes_no(latest.get('is_laggard'))}",
                f"Status: {latest.get('status', 'unknown')}",
            ]
        )

    lines.extend(["", "HISTORICAL LAGGARD OUTCOMES"])
    eligible = rows[(rows.get("status") == "ok") & (rows.get("is_laggard").astype(bool))].copy() if not rows.empty else pd.DataFrame()
    table = _sector_history_table(eligible)
    lines.extend(table if table else ["No eligible laggard history for this symbol."])
    lines.extend(
        [
            "",
            "Sources:",
            "- data/cache/<symbol>.csv local market cache",
            "- config/universe.csv fixed sector labels",
            "- src/research.py::run_sector_catch_up",
            "",
            "Warning: catch-up evidence is historical and does not guarantee future returns.",
        ]
    )
    _append_warnings(lines, warnings)
    return "\n".join(lines)


def _render_weekday_pattern(
    member: UniverseMember,
    observations: pd.DataFrame,
    warnings: list[str],
) -> str:
    lines = [
        f"Scenario 2 - Weekday / Multi-Day Pattern: {member.yahoo_symbol}",
        "",
        "1-DAY WEEKDAY PATTERN",
    ]
    ok = observations[observations["status"] == "ok"].copy() if not observations.empty else pd.DataFrame()
    weekday_rows = ok[(ok["pattern_type"] == "weekday") & (ok["holding_days"] == 1)] if not ok.empty else pd.DataFrame()
    lines.extend(_weekday_table(weekday_rows) or ["No eligible weekday observations."])
    lines.extend(["", "MULTI-DAY HOLDING SUMMARY"])
    lines.extend(_holding_table(ok) or ["No eligible multi-day observations."])
    lines.extend(["", "MARKET REGIME RESULTS"])
    lines.extend(_regime_table(ok) or ["No eligible regime rows."])
    lines.extend(["", "OUT-OF-SAMPLE RESULTS"])
    lines.extend(_split_table(ok) or ["No configured out-of-sample rows."])
    lines.extend(
        [
            "",
            "TRANSACTION COST",
            "Returns include configured trading cost and slippage through cost_adjusted_return.",
            "",
            "MULTIPLE-TESTING RISK",
            "Weekday effects are exploratory. Testing many weekdays, holding periods and regimes can produce apparently successful patterns by chance; selection/unseen split and regime tables are included so the result is not judged only on the full sample.",
            "",
            "Sources:",
            "- data/cache/<symbol>.csv local market cache",
            "- data/cache/XU100_IS.csv benchmark regime cache when available",
            "- config/settings.yaml cost, slippage and unseen split",
            "- src/research.py::run_weekday_patterns",
        ]
    )
    _append_warnings(lines, warnings)
    return "\n".join(lines)


def _render_technical_reversal(
    member: UniverseMember,
    enriched: pd.DataFrame,
    events: pd.DataFrame,
    observations: pd.DataFrame,
    warnings: list[str],
) -> str:
    lines = [f"Scenario 3 - Technical Reversal: {member.yahoo_symbol}", ""]
    if enriched.empty:
        lines.append("No technical frame available.")
    else:
        latest = enriched.dropna(subset=["close"]).iloc[-1]
        kama_slope = _safe_float(enriched["kama_10"].diff().iloc[-1]) if "kama_10" in enriched else None
        direction = _safe_float(latest.get("supertrend_direction"))
        lines.extend(
            [
                "CURRENT TECHNICAL SETUP",
                f"Date: {latest.get('date')}",
                f"Close: {_fmt_number(latest.get('close'))}",
                f"Lower Bollinger touch in last 20 days: {_yes_no(_recent_event(events, 'bollinger', 'lower_band_touch', latest.get('date')))}",
                f"RSI: {_fmt_number(latest.get('rsi_14'))}",
                f"Relative volume: {_fmt_number(latest.get('relative_volume'))}",
                f"KAMA slope: {_trend_from_number(kama_slope)}",
                f"Supertrend: {'bullish' if direction and direction > 0 else 'bearish' if direction and direction < 0 else 'unknown'}",
            ]
        )

    latest_event = _latest_event(events)
    lines.extend(["", "HISTORICAL EVENT TEST"])
    if latest_event is None:
        lines.append("No detected technical events.")
    else:
        lines.append(f"Reference event: {latest_event['event_family']} / {latest_event['event_type']} on {latest_event['event_date']}")
        similar = observations[
            (observations["status"] == "ok")
            & (observations["event_family"].astype(str) == str(latest_event["event_family"]))
            & (observations["event_type"].astype(str) == str(latest_event["event_type"]))
        ].copy() if not observations.empty else pd.DataFrame()
        lines.extend(_technical_horizon_table(similar) or ["No eligible forward-return observations for this event."])
    lines.extend(
        [
            "",
            "Sources:",
            "- src/indicators.py deterministic RSI, Bollinger, KAMA, Supertrend and volume indicators",
            "- src/events.py deterministic event detectors",
            "- src/research.py::run_technical_reversals",
            "",
            "Warning: technical reversal statistics are historical event frequencies, not a prediction.",
        ]
    )
    _append_warnings(lines, warnings)
    return "\n".join(lines)


def _render_fundamentals_reaction(
    member: UniverseMember,
    rows: pd.DataFrame,
    warnings: list[str],
) -> str:
    lines = [f"Scenario 4 - Quarterly Fundamentals + Price Reaction: {member.yahoo_symbol}", ""]
    if rows.empty:
        lines.append("No point-in-time fundamentals reaction rows available.")
    else:
        latest_period = rows["period_end"].max()
        latest = rows[rows["period_end"] == latest_period].copy()
        disclosure = latest["disclosure_timestamp"].iloc[0]
        profile = latest["metric_profile"].iloc[0]
        primary_metric = "net_interest_income" if profile == "bank" else "revenue"
        lines.extend(
            [
                "DISCLOSURE EVENT",
                f"Latest period: {latest_period}",
                f"Disclosure timestamp used as signal time: {disclosure}",
                f"Metric profile: {profile}",
                "",
                "FUNDAMENTAL METRIC CHANGES",
            ]
        )
        lines.extend(_fundamental_metric_table(latest) or ["No metric-change rows."])
        lines.extend(
            [
                "",
                "PRICE REACTION AFTER DISCLOSURE",
                f"Primary metric for return table: {primary_metric}",
            ]
        )
        primary = latest[latest["metric_name"] == primary_metric].copy()
        if primary.empty:
            primary = latest.copy()
        lines.extend(_fundamental_reaction_table(primary) or ["No eligible price-reaction rows."])
        lines.extend(
            [
                "",
                "Unavailable with current yfinance fallback:",
                "- EBITDA",
                "- EBITDA margin",
                "- Net debt / EBITDA",
                "These metrics are not invented; available operating profit/margin and cash-flow fields are reported instead.",
            ]
        )
    lines.extend(
        [
            "",
            "Sources:",
            "- data/fundamentals/fundamentals.csv yfinance fallback with synthetic disclosure timestamps",
            "- data/cache/<symbol>.csv local market cache",
            "- data/cache/XU100_IS.csv benchmark cache",
            "- src/research.py::run_quarterly_fundamentals",
            "",
            "Warning: quarter-end is not used as signal time; disclosure_timestamp controls the entry date.",
        ]
    )
    _append_warnings(lines, warnings)
    return "\n".join(lines)


def _sector_history_table(rows: pd.DataFrame) -> list[str]:
    if rows.empty:
        return []
    lines = ["| Horizon | Occurrences | Average future relative | Median future relative | Win rate | False positive rate |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for horizon, group in rows.groupby("horizon"):
        returns = pd.to_numeric(group["future_relative_return"], errors="coerce").dropna()
        false_positive = group["false_positive"].astype(bool)
        lines.append(
            f"| {int(horizon)}D | {len(returns)} | {_fmt_pct(returns.mean())} | {_fmt_pct(returns.median())} | {_fmt_pct((returns > 0).mean())} | {_fmt_pct(false_positive.mean())} |"
        )
    return lines


def _weekday_table(rows: pd.DataFrame) -> list[str]:
    if rows.empty:
        return []
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    lines = ["| Weekday | Occurrences | Average return | Median return | Win rate | Avg cost-adjusted |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for day in order:
        group = rows[rows["pattern_name"] == day]
        if group.empty:
            continue
        returns = pd.to_numeric(group["gross_return"], errors="coerce").dropna()
        cost = pd.to_numeric(group["cost_adjusted_return"], errors="coerce").dropna()
        lines.append(f"| {day} | {len(returns)} | {_fmt_pct(returns.mean())} | {_fmt_pct(returns.median())} | {_fmt_pct((returns > 0).mean())} | {_fmt_pct(cost.mean())} |")
    return lines


def _holding_table(rows: pd.DataFrame) -> list[str]:
    if rows.empty:
        return []
    lines = ["| Holding days | Occurrences | Average return | Median return | Win rate | Avg cost-adjusted |", "| ---: | ---: | ---: | ---: | ---: | ---: |"]
    for holding, group in rows.groupby("holding_days"):
        returns = pd.to_numeric(group["gross_return"], errors="coerce").dropna()
        cost = pd.to_numeric(group["cost_adjusted_return"], errors="coerce").dropna()
        lines.append(f"| {int(holding)} | {len(returns)} | {_fmt_pct(returns.mean())} | {_fmt_pct(returns.median())} | {_fmt_pct((returns > 0).mean())} | {_fmt_pct(cost.mean())} |")
    return lines


def _regime_table(rows: pd.DataFrame) -> list[str]:
    if rows.empty or "market_regime" not in rows:
        return []
    lines = ["| Market regime | Occurrences | Average return | Win rate |", "| --- | ---: | ---: | ---: |"]
    for regime, group in rows.groupby("market_regime", dropna=False):
        returns = pd.to_numeric(group["gross_return"], errors="coerce").dropna()
        lines.append(f"| {regime} | {len(returns)} | {_fmt_pct(returns.mean())} | {_fmt_pct((returns > 0).mean())} |")
    return lines


def _split_table(rows: pd.DataFrame) -> list[str]:
    if rows.empty or "period_split" not in rows:
        return []
    lines = ["| Period split | Occurrences | Average return | Median return | Win rate |", "| --- | ---: | ---: | ---: | ---: |"]
    for split, group in rows.groupby("period_split", dropna=False):
        returns = pd.to_numeric(group["gross_return"], errors="coerce").dropna()
        lines.append(f"| {split} | {len(returns)} | {_fmt_pct(returns.mean())} | {_fmt_pct(returns.median())} | {_fmt_pct((returns > 0).mean())} |")
    return lines


def _technical_horizon_table(rows: pd.DataFrame) -> list[str]:
    if rows.empty:
        return []
    lines = ["| Horizon | Events | Positive moves | Median return | Bounce rate |", "| ---: | ---: | ---: | ---: | ---: |"]
    for horizon, group in rows.groupby("horizon"):
        returns = pd.to_numeric(group["forward_return"], errors="coerce").dropna()
        lines.append(f"| {int(horizon)} | {len(returns)} | {int((returns > 0).sum())} | {_fmt_pct(returns.median())} | {_fmt_pct((returns > 0).mean())} |")
    return lines


def _fundamental_metric_table(rows: pd.DataFrame) -> list[str]:
    if rows.empty:
        return []
    one_per_metric = rows.sort_values("horizon").drop_duplicates("metric_name")
    lines = ["| Metric | QoQ change | YoY change | Current value |", "| --- | ---: | ---: | ---: |"]
    preferred = ["revenue", "operating_profit", "operating_margin", "operating_cash_flow", "free_cash_flow", "debt_to_assets", "net_interest_income", "net_income"]
    for metric in preferred:
        metric_rows = one_per_metric[one_per_metric["metric_name"] == metric]
        if metric_rows.empty:
            continue
        row = metric_rows.iloc[0]
        lines.append(f"| {metric} | {_fmt_pct(row.get('qoq_change'))} | {_fmt_pct(row.get('yoy_change'))} | {_fmt_number(row.get('current_value'))} |")
    return lines


def _fundamental_reaction_table(rows: pd.DataFrame) -> list[str]:
    ok = rows[rows["status"] == "ok"].copy()
    if ok.empty:
        return []
    lines = ["| Horizon | Stock return | Stock - XU100 | Stock - sector median | Sector peer count | Entry -> Exit |", "| ---: | ---: | ---: | ---: | ---: | --- |"]
    for _, row in ok.sort_values("horizon").iterrows():
        lines.append(
            f"| {int(row['horizon'])}D | {_fmt_pct(row.get('post_disclosure_return'))} | {_fmt_pct(row.get('benchmark_relative_return'))} | {_fmt_pct(row.get('sector_relative_return'))} | {_fmt_int(row.get('sector_peer_count'))} | {row.get('entry_date')} -> {row.get('exit_date')} |"
        )
    return lines


def _resolve_member(requested_symbol: str, universe: list[UniverseMember]) -> UniverseMember:
    symbol = requested_symbol.strip().upper()
    for member in universe:
        if symbol in {member.ticker.upper(), member.yahoo_symbol.upper()}:
            return member
    if not symbol.endswith(".IS"):
        return _resolve_member(f"{symbol}.IS", universe)
    raise ValueError(f"{requested_symbol} is not in the fixed universe")


def _load_prices(
    universe: list[UniverseMember],
    cache_dir: str | Path,
    warnings: list[str],
) -> dict[str, pd.DataFrame]:
    prices: dict[str, pd.DataFrame] = {}
    for member in universe:
        frame = _load_single_price(member, cache_dir, warnings)
        if frame is not None:
            prices[member.yahoo_symbol] = frame
    return prices


def _load_single_price(
    member: UniverseMember,
    cache_dir: str | Path,
    warnings: list[str],
) -> pd.DataFrame | None:
    try:
        return read_price_cache(cache_dir, member.yahoo_symbol)
    except Exception as exc:
        warnings.append(f"{member.yahoo_symbol}: price cache unavailable ({exc})")
        return None


def _load_optional_price(symbol: str, cache_dir: str | Path, warnings: list[str]) -> pd.DataFrame | None:
    try:
        return read_price_cache(cache_dir, symbol)
    except Exception as exc:
        warnings.append(f"{symbol}: optional benchmark cache unavailable ({exc})")
        return None


def _write_report(text: str, output_path: str | Path | None, prefix: str, symbol: str) -> Path:
    path = Path(output_path) if output_path else DEFAULT_SCENARIO_REPORT_DIR / f"{prefix}_{_safe_symbol(symbol)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _append_warnings(lines: list[str], warnings: list[str]) -> None:
    if warnings:
        lines.extend(["", "Runtime Warnings:"])
        lines.extend(f"- {warning}" for warning in warnings[:10])
        if len(warnings) > 10:
            lines.append(f"- ... {len(warnings) - 10} more warnings")


def _latest_event(events: pd.DataFrame) -> pd.Series | None:
    if events.empty:
        return None
    return events.sort_values("event_date").iloc[-1]


def _recent_event(events: pd.DataFrame, family: str, event_type: str, latest_date: object) -> bool:
    if events.empty:
        return False
    latest = pd.to_datetime(latest_date, errors="coerce")
    if pd.isna(latest):
        return False
    frame = events.copy()
    frame["event_dt"] = pd.to_datetime(frame["event_date"], errors="coerce")
    cutoff = latest - pd.Timedelta(days=20)
    return bool(
        (
            (frame["event_family"].astype(str) == family)
            & (frame["event_type"].astype(str) == event_type)
            & (frame["event_dt"] >= cutoff)
            & (frame["event_dt"] <= latest)
        ).any()
    )


def _safe_symbol(symbol: str) -> str:
    return symbol.replace(".", "_").replace("/", "_")


def _safe_float(value: object) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _fmt_pct(value: object) -> str:
    number = _safe_float(value)
    if number is None:
        return "n/a"
    return f"{number * 100:+.2f}%"


def _fmt_number(value: object) -> str:
    number = _safe_float(value)
    if number is None:
        return "n/a"
    return f"{number:,.2f}"


def _fmt_int(value: object) -> str:
    number = _safe_float(value)
    if number is None:
        return "n/a"
    return f"{int(number):,}"


def _yes_no(value: object) -> str:
    return "yes" if bool(value) else "no"


def _trend_from_number(value: object) -> str:
    number = _safe_float(value)
    if number is None:
        return "unknown"
    if number > 0:
        return "turning/improving"
    if number < 0:
        return "weakening"
    return "flat"
