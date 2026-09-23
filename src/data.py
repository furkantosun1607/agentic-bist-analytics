"""Data adapters, cache helpers, and point-in-time validation hooks."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

import pandas as pd

REQUIRED_UNIVERSE_COLUMNS = ("ticker", "yahoo_symbol", "sector")
EXPECTED_UNIVERSE_SIZE = 30
DEFAULT_UNIVERSE_PATH = Path(__file__).resolve().parents[1] / "config" / "universe.csv"
PRICE_CACHE_COLUMNS = (
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "source",
    "download_timestamp",
)


@dataclass(frozen=True)
class UniverseMember:
    """A single fixed-universe stock entry."""

    ticker: str
    yahoo_symbol: str
    sector: str


@dataclass(frozen=True)
class MissingSymbol:
    symbol: str
    reason: str


@dataclass(frozen=True)
class MarketDataResult:
    prices: dict[str, pd.DataFrame]
    missing_symbols: tuple[MissingSymbol, ...]
    cache_dir: Path
    benchmark_symbol: str
    download_timestamp: str


class PriceProvider(Protocol):
    def download(self, symbol: str, start: str, end: str | None) -> pd.DataFrame:
        """Download raw OHLCV data for a symbol."""


class YFinancePriceProvider:
    """Yahoo Finance/yfinance price provider."""

    def download(self, symbol: str, start: str, end: str | None) -> pd.DataFrame:
        import yfinance as yf

        return yf.download(
            symbol,
            start=start,
            end=end,
            progress=False,
            auto_adjust=False,
            actions=False,
        )


def load_universe(path: str | Path = DEFAULT_UNIVERSE_PATH) -> list[UniverseMember]:
    """Load the fixed study universe from CSV."""

    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [
            UniverseMember(
                ticker=(row.get("ticker") or "").strip(),
                yahoo_symbol=(row.get("yahoo_symbol") or "").strip(),
                sector=(row.get("sector") or "").strip(),
            )
            for row in reader
        ]

    return rows


def validate_universe(
    members: list[UniverseMember],
    expected_size: int = EXPECTED_UNIVERSE_SIZE,
) -> list[str]:
    """Return validation errors for the fixed universe."""

    errors: list[str] = []

    if len(members) != expected_size:
        errors.append(f"expected {expected_size} universe members, found {len(members)}")

    tickers = [member.ticker for member in members]
    duplicate_tickers = sorted({ticker for ticker in tickers if tickers.count(ticker) > 1})
    if duplicate_tickers:
        errors.append(f"duplicate tickers: {', '.join(duplicate_tickers)}")

    for index, member in enumerate(members, start=1):
        if not member.ticker:
            errors.append(f"row {index}: missing ticker")
        if not member.yahoo_symbol:
            errors.append(f"row {index}: missing yahoo_symbol")
        if not member.sector:
            errors.append(f"row {index}: missing sector")
        if member.yahoo_symbol and not member.yahoo_symbol.endswith(".IS"):
            errors.append(f"row {index}: yahoo_symbol must end with .IS")

    return errors


def fetch_market_data(
    symbols: list[str],
    benchmark_symbol: str,
    start_date: str,
    end_date: str | None,
    cache_dir: str | Path,
    provider: PriceProvider | None = None,
    source: str = "yahoo_finance",
    download_timestamp: str | None = None,
) -> MarketDataResult:
    """Fetch stock and benchmark prices, then cache normalized OHLCV records."""

    active_provider = provider or YFinancePriceProvider()
    timestamp = download_timestamp or datetime.now(UTC).isoformat()
    cache_path = Path(cache_dir)
    unique_symbols = _dedupe_symbols([*symbols, benchmark_symbol])
    prices: dict[str, pd.DataFrame] = {}
    missing: list[MissingSymbol] = []

    for symbol in unique_symbols:
        try:
            raw_prices = active_provider.download(symbol, start_date, end_date)
            normalized = normalize_price_frame(
                symbol=symbol,
                raw_prices=raw_prices,
                source=source,
                download_timestamp=timestamp,
            )
        except Exception as exc:
            missing.append(MissingSymbol(symbol=symbol, reason=str(exc)))
            continue

        prices[symbol] = normalized
        write_price_cache(normalized, cache_path, symbol)

    return MarketDataResult(
        prices=prices,
        missing_symbols=tuple(missing),
        cache_dir=cache_path,
        benchmark_symbol=benchmark_symbol,
        download_timestamp=timestamp,
    )


def normalize_price_frame(
    symbol: str,
    raw_prices: pd.DataFrame,
    source: str,
    download_timestamp: str,
) -> pd.DataFrame:
    """Normalize provider OHLCV data to the project cache schema."""

    if raw_prices is None or raw_prices.empty:
        raise ValueError("no price rows returned")

    frame = raw_prices.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)

    if "Date" not in frame.columns:
        frame = frame.reset_index()

    rename_map = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    }
    frame = frame.rename(columns=rename_map)

    required_columns = ("date", "open", "high", "low", "close", "volume")
    missing_columns = [column for column in required_columns if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"missing OHLCV columns: {', '.join(missing_columns)}")

    if "adj_close" not in frame.columns:
        frame["adj_close"] = frame["close"]

    normalized = frame.loc[:, ["date", "open", "high", "low", "close", "adj_close", "volume"]]
    normalized = normalized.dropna(subset=["date", "open", "high", "low", "close"])
    if normalized.empty:
        raise ValueError("no complete OHLC rows returned")

    normalized.insert(0, "symbol", symbol)
    normalized["date"] = pd.to_datetime(normalized["date"]).dt.date.astype(str)
    normalized["volume"] = normalized["volume"].fillna(0).astype("int64")
    normalized["source"] = source
    normalized["download_timestamp"] = download_timestamp

    return normalized.loc[:, list(PRICE_CACHE_COLUMNS)].sort_values("date").reset_index(drop=True)


def write_price_cache(prices: pd.DataFrame, cache_dir: str | Path, symbol: str) -> Path:
    """Write normalized price records to the symbol cache CSV."""

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    output_path = price_cache_path(cache_path, symbol)
    prices.to_csv(output_path, index=False)
    return output_path


def read_price_cache(cache_dir: str | Path, symbol: str) -> pd.DataFrame:
    """Read a normalized symbol price cache CSV."""

    return pd.read_csv(price_cache_path(Path(cache_dir), symbol))


def write_missing_symbols_report(
    missing_symbols: tuple[MissingSymbol, ...] | list[MissingSymbol],
    reports_dir: str | Path,
) -> Path:
    """Write a small CSV report for symbols that could not be fetched."""

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    output_path = reports_path / "missing_symbols.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["symbol", "reason"])
        writer.writeheader()
        for missing in missing_symbols:
            writer.writerow({"symbol": missing.symbol, "reason": missing.reason})

    return output_path


def price_cache_path(cache_dir: str | Path, symbol: str) -> Path:
    """Return the cache path for a symbol."""

    return Path(cache_dir) / f"{_safe_symbol_name(symbol)}.csv"


def _safe_symbol_name(symbol: str) -> str:
    return symbol.replace(".", "_").replace("/", "_")


def _dedupe_symbols(symbols: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for symbol in symbols:
        if symbol not in seen:
            seen.add(symbol)
            deduped.append(symbol)
    return deduped
