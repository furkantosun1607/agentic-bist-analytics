"""Research scenario orchestration for the four required analyses."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data import UniverseMember


SECTOR_CATCH_UP_COLUMNS = (
    "symbol",
    "ticker",
    "sector",
    "date",
    "peer_count",
    "status",
    "lookback_return",
    "peer_median_lookback_return",
    "catch_up_score",
    "rank_in_sector",
    "is_laggard",
    "horizon",
    "future_return",
    "peer_median_future_return",
    "future_relative_return",
    "false_positive",
)


@dataclass(frozen=True)
class ResearchError:
    scope: str
    message: str


@dataclass(frozen=True)
class SectorCatchUpResult:
    observations: pd.DataFrame
    errors: tuple[ResearchError, ...]


class ResearchInputError(ValueError):
    """Raised when research inputs are structurally invalid."""


def run_sector_catch_up(
    prices_by_symbol: dict[str, pd.DataFrame],
    universe: list[UniverseMember],
    lookback_days: int = 20,
    horizons: tuple[int, ...] = (5, 10, 20),
) -> SectorCatchUpResult:
    """Run the sector catch-up scenario on normalized price histories."""

    _validate_sector_catch_up_args(lookback_days, horizons)
    errors: list[ResearchError] = []

    try:
        price_panel = _build_sector_price_panel(prices_by_symbol, universe)
    except Exception as exc:
        return SectorCatchUpResult(
            observations=empty_sector_catch_up_frame(),
            errors=(ResearchError(scope="sector_catch_up", message=str(exc)),),
        )

    if price_panel.empty:
        return SectorCatchUpResult(
            observations=empty_sector_catch_up_frame(),
            errors=(ResearchError(scope="sector_catch_up", message="price panel is empty"),),
        )

    observations: list[pd.DataFrame] = []
    panel = price_panel.sort_values(["symbol", "date"]).copy()
    panel["lookback_return"] = panel.groupby("symbol")["close"].pct_change(lookback_days)

    for horizon in horizons:
        try:
            horizon_frame = _sector_catch_up_for_horizon(panel, horizon)
        except Exception as exc:
            errors.append(ResearchError(scope=f"horizon_{horizon}", message=str(exc)))
            continue

        observations.append(horizon_frame)

    if not observations:
        return SectorCatchUpResult(
            observations=empty_sector_catch_up_frame(),
            errors=tuple(errors)
            or (ResearchError(scope="sector_catch_up", message="no horizons were evaluated"),),
        )

    combined = pd.concat(observations, ignore_index=True)
    return SectorCatchUpResult(
        observations=combined.loc[:, list(SECTOR_CATCH_UP_COLUMNS)],
        errors=tuple(errors),
    )


def write_sector_catch_up_report(
    result: SectorCatchUpResult,
    output_path: str | Path,
    lookback_days: int = 20,
) -> Path:
    """Write a compact markdown report for sector catch-up results."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    observations = result.observations

    lines = [
        "# Sector Catch-Up Report",
        "",
        f"Lookback window: {lookback_days} trading days.",
        "Signals: laggards are rows where stock lookback return is below eligible peer median.",
        "Peer rule: same simplified sector, excluding the stock itself.",
        "",
    ]

    if observations.empty:
        lines.extend(
            [
                "Status: no observations generated.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"Data period: {observations['date'].min()} to {observations['date'].max()}.",
                f"Observation rows: {len(observations)}.",
                f"Symbols: {observations['symbol'].nunique()}.",
                "",
                "## Status Counts",
                "",
                observations["status"].value_counts().to_markdown(),
                "",
                "## Laggard Outcomes",
                "",
                _laggard_summary_markdown(observations),
                "",
            ]
        )

    if result.errors:
        lines.extend(["## Errors", ""])
        for error in result.errors:
            lines.append(f"- `{error.scope}`: {error.message}")
        lines.append("")

    lines.extend(
        [
            "Limitations:",
            "- This report is historical research output, not investment advice.",
            "- Results depend on cached price histories and fixed universe sector labels.",
            "- Fundamental, macro, news and video context are added in later phases.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def empty_sector_catch_up_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(SECTOR_CATCH_UP_COLUMNS))


def _sector_catch_up_for_horizon(panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
    frame = panel.copy()
    frame["future_return"] = frame.groupby("symbol")["close"].shift(-horizon) / frame["close"] - 1
    frame["peer_count"] = frame.groupby(["sector", "date"])["symbol"].transform("count") - 1
    frame["peer_median_lookback_return"] = _peer_median(
        frame,
        value_column="lookback_return",
    )
    frame["peer_median_future_return"] = _peer_median(
        frame,
        value_column="future_return",
    )
    frame["catch_up_score"] = (
        frame["lookback_return"] - frame["peer_median_lookback_return"]
    )
    frame["future_relative_return"] = (
        frame["future_return"] - frame["peer_median_future_return"]
    )
    frame["rank_in_sector"] = frame.groupby(["sector", "date"])["lookback_return"].rank(
        method="first",
        ascending=False,
    )
    frame["is_laggard"] = frame["catch_up_score"] < 0
    frame["horizon"] = horizon
    frame["status"] = "ok"
    frame.loc[frame["peer_count"] < 1, "status"] = "insufficient_peers"
    frame.loc[frame["lookback_return"].isna(), "status"] = "insufficient_history"
    frame.loc[frame["future_return"].isna(), "status"] = "insufficient_forward_history"
    frame.loc[
        frame["peer_median_future_return"].isna() & (frame["peer_count"] >= 1),
        "status",
    ] = "insufficient_peer_forward_history"
    frame["false_positive"] = (
        (frame["status"] == "ok")
        & frame["is_laggard"]
        & (frame["future_relative_return"] <= 0)
    )

    return frame.loc[:, list(SECTOR_CATCH_UP_COLUMNS)]


def _peer_median(frame: pd.DataFrame, value_column: str) -> pd.Series:
    peers = frame[["sector", "date", "symbol", value_column]].copy()
    merged = peers.merge(peers, on=["sector", "date"], suffixes=("", "_peer"))
    merged = merged[merged["symbol"] != merged["symbol_peer"]]
    medians = (
        merged.groupby(["symbol", "date"])[f"{value_column}_peer"]
        .median()
        .rename(f"peer_median_{value_column}")
        .reset_index()
    )
    aligned = frame[["symbol", "date"]].merge(medians, on=["symbol", "date"], how="left")
    return aligned[f"peer_median_{value_column}"]


def _build_sector_price_panel(
    prices_by_symbol: dict[str, pd.DataFrame],
    universe: list[UniverseMember],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    universe_by_symbol = {member.yahoo_symbol: member for member in universe}

    for symbol, prices in prices_by_symbol.items():
        try:
            _require_columns(prices, ["date", "close"], scope=symbol)
            member = universe_by_symbol.get(symbol)
            if member is None:
                raise ResearchInputError(f"{symbol} is not in the fixed universe")

            frame = prices.loc[:, ["date", "close"]].copy()
            frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date.astype(str)
            frame["close"] = pd.to_numeric(frame["close"], errors="raise")
            frame["symbol"] = symbol
            frame["ticker"] = member.ticker
            frame["sector"] = member.sector
            frames.append(frame)
        except Exception as exc:
            raise ResearchInputError(f"failed to prepare {symbol}: {exc}") from exc

    if not frames:
        return pd.DataFrame(columns=["symbol", "ticker", "sector", "date", "close"])

    panel = pd.concat(frames, ignore_index=True)
    return panel.loc[:, ["symbol", "ticker", "sector", "date", "close"]]


def _require_columns(frame: pd.DataFrame, columns: list[str], scope: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ResearchInputError(f"{scope} missing required columns: {', '.join(missing)}")


def _validate_sector_catch_up_args(lookback_days: int, horizons: tuple[int, ...]) -> None:
    if lookback_days <= 0:
        raise ResearchInputError("lookback_days must be positive")
    if not horizons:
        raise ResearchInputError("at least one horizon is required")
    invalid_horizons = [horizon for horizon in horizons if horizon <= 0]
    if invalid_horizons:
        raise ResearchInputError(f"horizons must be positive: {invalid_horizons}")


def _laggard_summary_markdown(observations: pd.DataFrame) -> str:
    ok_laggards = observations[(observations["status"] == "ok") & observations["is_laggard"]]
    if ok_laggards.empty:
        return "No eligible laggard observations."

    summary = (
        ok_laggards.groupby("horizon")
        .agg(
            observations=("symbol", "count"),
            average_future_relative_return=("future_relative_return", "mean"),
            median_future_relative_return=("future_relative_return", "median"),
            false_positives=("false_positive", "sum"),
        )
        .reset_index()
    )
    return summary.to_markdown(index=False)
