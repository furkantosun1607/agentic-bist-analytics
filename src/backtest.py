"""Point-in-time safe historical signal evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


BACKTEST_TRADE_COLUMNS = (
    "signal_id",
    "symbol",
    "source",
    "known_at",
    "direction",
    "horizon",
    "status",
    "entry_timing",
    "exit_timing",
    "entry_date",
    "entry_price",
    "exit_date",
    "exit_price",
    "gross_return",
    "trading_cost_bps",
    "slippage_bps",
    "total_cost_bps",
    "cost_adjusted_return",
    "benchmark_return",
    "benchmark_relative_return",
    "sector",
    "sector_benchmark_return",
    "sector_relative_return",
    "buy_hold_return",
)
BACKTEST_SUMMARY_COLUMNS = (
    "status",
    "signal_count",
    "trade_count",
    "symbol_count",
    "average_gross_return",
    "median_gross_return",
    "average_cost_adjusted_return",
    "median_cost_adjusted_return",
    "cumulative_return",
    "sharpe_ratio",
    "maximum_drawdown",
    "win_rate",
    "cumulative_benchmark_return",
    "benchmark_difference",
    "average_benchmark_relative_return",
    "average_sector_relative_return",
)
REQUIRED_SIGNAL_COLUMNS = ("signal_id", "symbol", "known_at")
SUPPORTED_DIRECTIONS = ("long",)


@dataclass(frozen=True)
class BacktestError:
    scope: str
    message: str


@dataclass(frozen=True)
class BacktestResult:
    trades: pd.DataFrame
    summary: pd.DataFrame
    errors: tuple[BacktestError, ...]


class BacktestInputError(ValueError):
    """Raised when backtest inputs are structurally invalid."""


def run_backtest(
    signals: pd.DataFrame,
    prices_by_symbol: dict[str, pd.DataFrame],
    benchmark_prices: pd.DataFrame | None = None,
    sector_benchmark_prices: dict[str, pd.DataFrame] | None = None,
    symbol_to_sector: dict[str, str] | None = None,
    default_horizon: int = 5,
    entry_timing: str = "next_trading_day_open",
    exit_timing: str = "close_after_horizon",
    trading_cost_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> BacktestResult:
    """Evaluate timestamped long-only signals without trading before they are knowable."""

    try:
        _validate_backtest_args(
            signals=signals,
            prices_by_symbol=prices_by_symbol,
            default_horizon=default_horizon,
            entry_timing=entry_timing,
            exit_timing=exit_timing,
            trading_cost_bps=trading_cost_bps,
            slippage_bps=slippage_bps,
        )
    except Exception as exc:
        return BacktestResult(
            trades=empty_backtest_trades_frame(),
            summary=empty_backtest_summary_frame(),
            errors=(BacktestError(scope="backtest", message=str(exc)),),
        )

    errors: list[BacktestError] = []
    prepared_prices: dict[str, pd.DataFrame] = {}
    for symbol, prices in prices_by_symbol.items():
        try:
            prepared_prices[symbol] = _prepare_price_frame(prices, scope=symbol)
        except Exception as exc:
            errors.append(BacktestError(scope=symbol, message=str(exc)))

    benchmark_frame = None
    if benchmark_prices is not None:
        try:
            benchmark_frame = _prepare_price_frame(benchmark_prices, scope="benchmark")
        except Exception as exc:
            errors.append(BacktestError(scope="benchmark", message=str(exc)))

    prepared_sector_benchmarks: dict[str, pd.DataFrame] = {}
    for sector, prices in (sector_benchmark_prices or {}).items():
        try:
            prepared_sector_benchmarks[sector] = _prepare_price_frame(
                prices,
                scope=f"sector benchmark {sector}",
            )
        except Exception as exc:
            errors.append(BacktestError(scope=f"sector benchmark {sector}", message=str(exc)))

    rows: list[dict[str, object]] = []
    for row_number, (_, signal) in enumerate(signals.iterrows(), start=2):
        try:
            rows.append(
                _backtest_signal(
                    signal=signal,
                    row_number=row_number,
                    prices_by_symbol=prepared_prices,
                    benchmark_prices=benchmark_frame,
                    sector_benchmark_prices=prepared_sector_benchmarks,
                    symbol_to_sector=symbol_to_sector or {},
                    default_horizon=default_horizon,
                    entry_timing=entry_timing,
                    exit_timing=exit_timing,
                    trading_cost_bps=trading_cost_bps,
                    slippage_bps=slippage_bps,
                )
            )
        except Exception as exc:
            signal_id = signal.get("signal_id", f"row_{row_number}")
            errors.append(BacktestError(scope=str(signal_id), message=str(exc)))

    if not rows:
        return BacktestResult(
            trades=empty_backtest_trades_frame(),
            summary=empty_backtest_summary_frame(),
            errors=tuple(errors)
            or (BacktestError(scope="backtest", message="no signals were evaluated"),),
        )

    trades = pd.DataFrame(rows).loc[:, list(BACKTEST_TRADE_COLUMNS)]
    return BacktestResult(
        trades=trades,
        summary=summarize_backtest(trades),
        errors=tuple(errors),
    )


def run_backtest_from_settings(
    signals: pd.DataFrame,
    prices_by_symbol: dict[str, pd.DataFrame],
    settings,
    benchmark_prices: pd.DataFrame | None = None,
    sector_benchmark_prices: dict[str, pd.DataFrame] | None = None,
    symbol_to_sector: dict[str, str] | None = None,
) -> BacktestResult:
    """Run backtest using timing, horizon and cost assumptions from settings."""

    backtest_config = settings.backtest
    if not backtest_config.horizons:
        return BacktestResult(
            trades=empty_backtest_trades_frame(),
            summary=empty_backtest_summary_frame(),
            errors=(
                BacktestError(
                    scope="settings",
                    message="settings.backtest.horizons must contain at least one value",
                ),
            ),
        )

    return run_backtest(
        signals=signals,
        prices_by_symbol=prices_by_symbol,
        benchmark_prices=benchmark_prices,
        sector_benchmark_prices=sector_benchmark_prices,
        symbol_to_sector=symbol_to_sector,
        default_horizon=int(backtest_config.horizons[0]),
        entry_timing=backtest_config.entry_timing,
        exit_timing=backtest_config.exit_timing,
        trading_cost_bps=float(backtest_config.trading_cost_bps),
        slippage_bps=float(backtest_config.slippage_bps),
    )


def summarize_backtest(trades: pd.DataFrame) -> pd.DataFrame:
    """Summarize eligible backtest trades with cost-adjusted risk metrics."""

    if trades.empty:
        return empty_backtest_summary_frame()

    ok = trades[trades["status"] == "ok"].copy()
    if ok.empty:
        return pd.DataFrame(
            [
                {
                    "status": "ok",
                    "signal_count": len(trades),
                    "trade_count": 0,
                    "symbol_count": 0,
                    "average_gross_return": pd.NA,
                    "median_gross_return": pd.NA,
                    "average_cost_adjusted_return": pd.NA,
                    "median_cost_adjusted_return": pd.NA,
                    "cumulative_return": pd.NA,
                    "sharpe_ratio": pd.NA,
                    "maximum_drawdown": pd.NA,
                    "win_rate": pd.NA,
                    "cumulative_benchmark_return": pd.NA,
                    "benchmark_difference": pd.NA,
                    "average_benchmark_relative_return": pd.NA,
                    "average_sector_relative_return": pd.NA,
                }
            ],
            columns=list(BACKTEST_SUMMARY_COLUMNS),
        )

    risk = calculate_risk_metrics(ok)
    return pd.DataFrame(
        [
            {
                "status": "ok",
                "signal_count": len(trades),
                "trade_count": len(ok),
                "symbol_count": ok["symbol"].nunique(),
                "average_gross_return": ok["gross_return"].mean(),
                "median_gross_return": ok["gross_return"].median(),
                "average_cost_adjusted_return": ok["cost_adjusted_return"].mean(),
                "median_cost_adjusted_return": ok["cost_adjusted_return"].median(),
                "cumulative_return": risk["cumulative_return"],
                "sharpe_ratio": risk["sharpe_ratio"],
                "maximum_drawdown": risk["maximum_drawdown"],
                "win_rate": risk["win_rate"],
                "cumulative_benchmark_return": risk["cumulative_benchmark_return"],
                "benchmark_difference": risk["benchmark_difference"],
                "average_benchmark_relative_return": ok[
                    "benchmark_relative_return"
                ].dropna().mean(),
                "average_sector_relative_return": ok["sector_relative_return"].dropna().mean(),
            }
        ],
        columns=list(BACKTEST_SUMMARY_COLUMNS),
    )


def calculate_risk_metrics(trades: pd.DataFrame) -> dict[str, object]:
    """Calculate deterministic trade-level risk metrics from eligible trades."""

    if trades.empty:
        return {
            "cumulative_return": pd.NA,
            "sharpe_ratio": pd.NA,
            "maximum_drawdown": pd.NA,
            "win_rate": pd.NA,
            "cumulative_benchmark_return": pd.NA,
            "benchmark_difference": pd.NA,
        }

    ordered = trades.copy()
    ordered["exit_sort"] = pd.to_datetime(ordered["exit_date"], errors="coerce")
    ordered = ordered.sort_values(["exit_sort", "signal_id"]).reset_index(drop=True)
    returns = pd.to_numeric(ordered["cost_adjusted_return"], errors="coerce").dropna()
    benchmark_returns = pd.to_numeric(ordered["benchmark_return"], errors="coerce").dropna()

    cumulative_return = _compound_return(returns)
    cumulative_benchmark_return = _compound_return(benchmark_returns)
    benchmark_difference = (
        cumulative_return - cumulative_benchmark_return
        if pd.notna(cumulative_return) and pd.notna(cumulative_benchmark_return)
        else pd.NA
    )

    return {
        "cumulative_return": cumulative_return,
        "sharpe_ratio": _sharpe_ratio(returns),
        "maximum_drawdown": _maximum_drawdown(returns),
        "win_rate": float((returns > 0).sum() / len(returns)) if len(returns) else pd.NA,
        "cumulative_benchmark_return": cumulative_benchmark_return,
        "benchmark_difference": benchmark_difference,
    }


def write_backtest_report(result: BacktestResult, output_path: str | Path) -> Path:
    """Write a compact markdown report for backtest results."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Backtest Report",
        "",
        "Timing: signals are entered on the first trading day after `known_at` and exited at the configured horizon close.",
        "Scope: trade generation, configured costs, benchmark hooks and risk metrics.",
        "",
    ]

    if result.trades.empty:
        lines.extend(["Status: no trades generated.", ""])
    else:
        lines.extend(
            [
                f"Signal rows: {len(result.trades)}.",
                f"Tradable rows: {len(result.trades[result.trades['status'] == 'ok'])}.",
                f"Symbols: {result.trades['symbol'].nunique()}.",
                "",
                "## Status Counts",
                "",
                result.trades["status"].value_counts().to_markdown(),
                "",
            ]
        )

    if result.summary.empty:
        lines.extend(["## Summary", "", "No eligible trades.", ""])
    else:
        lines.extend(["## Summary", "", result.summary.to_markdown(index=False), ""])

    if result.errors:
        lines.extend(["## Errors", ""])
        for error in result.errors:
            lines.append(f"- `{error.scope}`: {error.message}")
        lines.append("")

    lines.extend(
        [
            "Limitations:",
            "- This report is historical research output, not investment advice.",
            "- Sharpe ratio is calculated on trade-level cost-adjusted returns, not daily portfolio returns.",
            "- Benchmark and sector benchmark returns are reported only when matching benchmark histories are provided.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def empty_backtest_trades_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(BACKTEST_TRADE_COLUMNS))


def empty_backtest_summary_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(BACKTEST_SUMMARY_COLUMNS))


def _backtest_signal(
    signal: pd.Series,
    row_number: int,
    prices_by_symbol: dict[str, pd.DataFrame],
    benchmark_prices: pd.DataFrame | None,
    sector_benchmark_prices: dict[str, pd.DataFrame],
    symbol_to_sector: dict[str, str],
    default_horizon: int,
    entry_timing: str,
    exit_timing: str,
    trading_cost_bps: float,
    slippage_bps: float,
) -> dict[str, object]:
    signal_id = _required_text(signal, "signal_id")
    symbol = _required_text(signal, "symbol")
    source = _optional_text(signal, "source") or "unspecified"
    known_at = _required_timestamp(signal, "known_at")
    direction = (_optional_text(signal, "direction") or "long").lower()
    horizon = _optional_positive_int(signal, "horizon", default_horizon)
    sector = symbol_to_sector.get(symbol)
    row = _base_trade_row(
        signal_id=signal_id,
        symbol=symbol,
        source=source,
        known_at=known_at,
        direction=direction,
        horizon=horizon,
        entry_timing=entry_timing,
        exit_timing=exit_timing,
        trading_cost_bps=trading_cost_bps,
        slippage_bps=slippage_bps,
        sector=sector,
    )

    if direction not in SUPPORTED_DIRECTIONS:
        row["status"] = "unsupported_direction"
        return row

    prices = prices_by_symbol.get(symbol)
    if prices is None:
        row["status"] = "missing_price_history"
        return row

    known_date = pd.to_datetime(known_at, errors="raise").date()
    entry_index = prices.index[prices["date"].dt.date > known_date]
    if len(entry_index) == 0:
        row["status"] = "insufficient_forward_history"
        return row

    entry_pos = int(entry_index[0])
    exit_pos = entry_pos + horizon
    entry = prices.iloc[entry_pos]
    row["entry_date"] = entry["date"].date().isoformat()
    row["entry_price"] = float(entry["entry_price"])
    row["buy_hold_return"] = _return_between_prices(
        entry_price=float(prices.iloc[0]["close"]),
        exit_price=float(entry["close"]),
    )

    if exit_pos >= len(prices):
        row["status"] = "insufficient_forward_history"
        return row

    exit_row = prices.iloc[exit_pos]
    row["exit_date"] = exit_row["date"].date().isoformat()
    row["exit_price"] = float(exit_row["close"])
    row["gross_return"] = _return_between_prices(
        entry_price=float(entry["entry_price"]),
        exit_price=float(exit_row["close"]),
    )
    total_cost = _total_cost_rate(trading_cost_bps, slippage_bps)
    row["cost_adjusted_return"] = row["gross_return"] - total_cost
    row["buy_hold_return"] = _return_between_prices(
        entry_price=float(prices.iloc[0]["close"]),
        exit_price=float(exit_row["close"]),
    )

    benchmark_return = _benchmark_return_for_dates(
        benchmark_prices,
        entry_date=row["entry_date"],
        exit_date=row["exit_date"],
    )
    row["benchmark_return"] = benchmark_return
    if pd.notna(benchmark_return):
        row["benchmark_relative_return"] = row["gross_return"] - benchmark_return

    if sector is not None:
        sector_return = _benchmark_return_for_dates(
            sector_benchmark_prices.get(sector),
            entry_date=row["entry_date"],
            exit_date=row["exit_date"],
        )
        row["sector_benchmark_return"] = sector_return
        if pd.notna(sector_return):
            row["sector_relative_return"] = row["gross_return"] - sector_return

    return row


def _base_trade_row(
    signal_id: str,
    symbol: str,
    source: str,
    known_at: str,
    direction: str,
    horizon: int,
    entry_timing: str,
    exit_timing: str,
    sector: str | None,
    trading_cost_bps: float,
    slippage_bps: float,
) -> dict[str, object]:
    total_cost_bps = float(trading_cost_bps) + float(slippage_bps)
    return {
        "signal_id": signal_id,
        "symbol": symbol,
        "source": source,
        "known_at": known_at,
        "direction": direction,
        "horizon": horizon,
        "status": "ok",
        "entry_timing": entry_timing,
        "exit_timing": exit_timing,
        "entry_date": pd.NA,
        "entry_price": pd.NA,
        "exit_date": pd.NA,
        "exit_price": pd.NA,
        "gross_return": pd.NA,
        "trading_cost_bps": float(trading_cost_bps),
        "slippage_bps": float(slippage_bps),
        "total_cost_bps": total_cost_bps,
        "cost_adjusted_return": pd.NA,
        "benchmark_return": pd.NA,
        "benchmark_relative_return": pd.NA,
        "sector": sector,
        "sector_benchmark_return": pd.NA,
        "sector_relative_return": pd.NA,
        "buy_hold_return": pd.NA,
    }


def _benchmark_return_for_dates(
    benchmark_prices: pd.DataFrame | None,
    entry_date: object,
    exit_date: object,
) -> float | object:
    if benchmark_prices is None or pd.isna(entry_date) or pd.isna(exit_date):
        return pd.NA

    entry_match = benchmark_prices[benchmark_prices["date"].dt.date.astype(str) == str(entry_date)]
    exit_match = benchmark_prices[benchmark_prices["date"].dt.date.astype(str) == str(exit_date)]
    if entry_match.empty or exit_match.empty:
        return pd.NA

    return _return_between_prices(
        entry_price=float(entry_match.iloc[0]["close"]),
        exit_price=float(exit_match.iloc[0]["close"]),
    )


def _return_between_prices(entry_price: float, exit_price: float) -> float:
    return float(exit_price / entry_price - 1)


def _total_cost_rate(trading_cost_bps: float, slippage_bps: float) -> float:
    return float(trading_cost_bps + slippage_bps) / 10000


def _compound_return(returns: pd.Series) -> float | object:
    if returns.empty:
        return pd.NA
    return float((1 + returns).prod() - 1)


def _sharpe_ratio(returns: pd.Series) -> float | object:
    if len(returns) < 2:
        return pd.NA
    standard_deviation = returns.std(ddof=1)
    if pd.isna(standard_deviation) or standard_deviation == 0:
        return pd.NA
    return float((returns.mean() / standard_deviation) * (len(returns) ** 0.5))


def _maximum_drawdown(returns: pd.Series) -> float | object:
    if returns.empty:
        return pd.NA
    equity = (1 + returns).cumprod()
    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1
    return float(drawdown.min())


def _prepare_price_frame(prices: pd.DataFrame, scope: str) -> pd.DataFrame:
    _require_columns(prices, ["date", "close"], scope=scope)
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["close"] = pd.to_numeric(frame["close"], errors="raise")
    if "open" in frame.columns:
        frame["entry_price"] = pd.to_numeric(frame["open"], errors="raise")
    else:
        frame["entry_price"] = frame["close"]

    frame = frame.sort_values("date").reset_index(drop=True)
    if frame["date"].duplicated().any():
        raise BacktestInputError(f"{scope} contains duplicate dates")
    if (frame["close"] <= 0).any() or (frame["entry_price"] <= 0).any():
        raise BacktestInputError(f"{scope} contains non-positive prices")

    return frame.loc[:, ["date", "entry_price", "close"]]


def _validate_backtest_args(
    signals: pd.DataFrame,
    prices_by_symbol: dict[str, pd.DataFrame],
    default_horizon: int,
    entry_timing: str,
    exit_timing: str,
    trading_cost_bps: float,
    slippage_bps: float,
) -> None:
    if signals is None or signals.empty:
        raise BacktestInputError("signals are empty")
    _require_columns(signals, list(REQUIRED_SIGNAL_COLUMNS), scope="signals")
    if not prices_by_symbol:
        raise BacktestInputError("prices_by_symbol is empty")
    if default_horizon <= 0:
        raise BacktestInputError("default_horizon must be positive")
    if entry_timing != "next_trading_day_open":
        raise BacktestInputError("entry_timing must be next_trading_day_open")
    if exit_timing != "close_after_horizon":
        raise BacktestInputError("exit_timing must be close_after_horizon")
    if trading_cost_bps < 0:
        raise BacktestInputError("trading_cost_bps cannot be negative")
    if slippage_bps < 0:
        raise BacktestInputError("slippage_bps cannot be negative")
    if trading_cost_bps + slippage_bps <= 0:
        raise BacktestInputError("trading_cost_bps plus slippage_bps must be nonzero")


def _require_columns(frame: pd.DataFrame, columns: list[str], scope: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise BacktestInputError(f"{scope} missing required columns: {', '.join(missing)}")


def _required_text(row: pd.Series, column: str) -> str:
    value = row.get(column)
    if pd.isna(value) or str(value).strip() == "":
        raise BacktestInputError(f"missing required value in row: {column}")
    return str(value).strip()


def _optional_text(row: pd.Series, column: str) -> str | None:
    if column not in row.index:
        return None
    value = row.get(column)
    if pd.isna(value) or str(value).strip() == "":
        return None
    return str(value).strip()


def _required_timestamp(row: pd.Series, column: str) -> str:
    value = _required_text(row, column)
    try:
        return pd.to_datetime(value, errors="raise").isoformat()
    except Exception as exc:
        raise BacktestInputError(f"invalid timestamp in {column}: {value}") from exc


def _optional_positive_int(row: pd.Series, column: str, default: int) -> int:
    if column not in row.index or pd.isna(row.get(column)) or str(row.get(column)).strip() == "":
        return default
    try:
        value = int(row.get(column))
    except Exception as exc:
        raise BacktestInputError(f"invalid integer in {column}: {row.get(column)}") from exc
    if value <= 0:
        raise BacktestInputError(f"{column} must be positive")
    return value
