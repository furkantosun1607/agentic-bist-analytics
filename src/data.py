"""Data adapters, cache helpers, and point-in-time validation hooks."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


REQUIRED_UNIVERSE_COLUMNS = ("ticker", "yahoo_symbol", "sector")
EXPECTED_UNIVERSE_SIZE = 30
DEFAULT_UNIVERSE_PATH = Path(__file__).resolve().parents[1] / "config" / "universe.csv"


@dataclass(frozen=True)
class UniverseMember:
    """A single fixed-universe stock entry."""

    ticker: str
    yahoo_symbol: str
    sector: str


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
