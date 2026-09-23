"""Technical event detectors for scenario 3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd


EVENT_COLUMNS = (
    "symbol",
    "event_family",
    "event_type",
    "event_date",
    "known_at",
    "value",
    "reference",
    "details",
)


@dataclass(frozen=True)
class DetectorError:
    detector: str
    message: str


@dataclass(frozen=True)
class EventDetectionResult:
    events: pd.DataFrame
    errors: tuple[DetectorError, ...]


class EventDetectionError(ValueError):
    """Raised when a detector cannot evaluate the provided frame."""


def detect_all_events(frame: pd.DataFrame, symbol: str | None = None) -> EventDetectionResult:
    """Run all event detectors and collect errors without hiding their source."""

    detectors: tuple[tuple[str, Callable[[pd.DataFrame, str | None], pd.DataFrame]], ...] = (
        ("bollinger", detect_bollinger_events),
        ("rsi", detect_rsi_events),
        ("supertrend", detect_supertrend_events),
        ("kama", detect_kama_events),
        ("ichimoku", detect_ichimoku_events),
        ("support_resistance", detect_support_resistance_events),
    )
    event_frames: list[pd.DataFrame] = []
    errors: list[DetectorError] = []

    for detector_name, detector in detectors:
        try:
            detected = detector(frame, symbol=symbol)
        except Exception as exc:
            errors.append(DetectorError(detector=detector_name, message=str(exc)))
            continue

        if not detected.empty:
            event_frames.append(detected)

    if event_frames:
        events = pd.concat(event_frames, ignore_index=True)
        events = events.sort_values(["event_date", "event_family", "event_type"]).reset_index(
            drop=True
        )
    else:
        events = empty_events_frame()

    return EventDetectionResult(events=events, errors=tuple(errors))


def detect_bollinger_events(frame: pd.DataFrame, symbol: str | None = None) -> pd.DataFrame:
    """Detect lower/middle/upper Bollinger tests and crosses."""

    _require_columns(
        frame,
        ["date", "close", "bb_lower", "bb_middle", "bb_upper"],
        "bollinger",
    )
    close = frame["close"].astype(float)
    events = [
        _events_from_mask(
            frame,
            symbol,
            family="bollinger",
            event_type="lower_band_touch",
            mask=(close <= frame["bb_lower"]) & (close.shift(1) > frame["bb_lower"].shift(1)),
            value=close,
            reference=frame["bb_lower"],
        ),
        _events_from_mask(
            frame,
            symbol,
            family="bollinger",
            event_type="middle_cross_up",
            mask=(close >= frame["bb_middle"]) & (close.shift(1) < frame["bb_middle"].shift(1)),
            value=close,
            reference=frame["bb_middle"],
        ),
        _events_from_mask(
            frame,
            symbol,
            family="bollinger",
            event_type="middle_cross_down",
            mask=(close <= frame["bb_middle"]) & (close.shift(1) > frame["bb_middle"].shift(1)),
            value=close,
            reference=frame["bb_middle"],
        ),
        _events_from_mask(
            frame,
            symbol,
            family="bollinger",
            event_type="upper_band_touch",
            mask=(close >= frame["bb_upper"]) & (close.shift(1) < frame["bb_upper"].shift(1)),
            value=close,
            reference=frame["bb_upper"],
        ),
    ]
    return _concat_events(events)


def detect_rsi_events(frame: pd.DataFrame, symbol: str | None = None) -> pd.DataFrame:
    """Detect RSI peaks/troughs and threshold exits."""

    _require_columns(frame, ["date", "rsi_14"], "rsi")
    rsi = frame["rsi_14"].astype(float)
    local_peak = (rsi.shift(1) < rsi) & (rsi.shift(-1) < rsi) & (rsi >= 70)
    local_trough = (rsi.shift(1) > rsi) & (rsi.shift(-1) > rsi) & (rsi <= 30)
    oversold_exit = (rsi > 30) & (rsi.shift(1) <= 30)
    overbought_exit = (rsi < 70) & (rsi.shift(1) >= 70)

    events = [
        _events_from_mask(
            frame,
            symbol,
            family="rsi",
            event_type="overbought_peak",
            mask=local_peak,
            value=rsi,
            reference=pd.Series(70.0, index=frame.index),
        ),
        _events_from_mask(
            frame,
            symbol,
            family="rsi",
            event_type="oversold_trough",
            mask=local_trough,
            value=rsi,
            reference=pd.Series(30.0, index=frame.index),
        ),
        _events_from_mask(
            frame,
            symbol,
            family="rsi",
            event_type="oversold_exit",
            mask=oversold_exit,
            value=rsi,
            reference=pd.Series(30.0, index=frame.index),
        ),
        _events_from_mask(
            frame,
            symbol,
            family="rsi",
            event_type="overbought_exit",
            mask=overbought_exit,
            value=rsi,
            reference=pd.Series(70.0, index=frame.index),
        ),
    ]
    return _concat_events(events)


def detect_supertrend_events(frame: pd.DataFrame, symbol: str | None = None) -> pd.DataFrame:
    """Detect Supertrend direction flips."""

    _require_columns(frame, ["date", "supertrend_direction"], "supertrend")
    direction = frame["supertrend_direction"].astype(float)
    flip_up = (direction == 1.0) & (direction.shift(1) == -1.0)
    flip_down = (direction == -1.0) & (direction.shift(1) == 1.0)

    return _concat_events(
        [
            _events_from_mask(
                frame,
                symbol,
                family="supertrend",
                event_type="flip_up",
                mask=flip_up,
                value=direction,
                reference=direction.shift(1),
            ),
            _events_from_mask(
                frame,
                symbol,
                family="supertrend",
                event_type="flip_down",
                mask=flip_down,
                value=direction,
                reference=direction.shift(1),
            ),
        ]
    )


def detect_kama_events(frame: pd.DataFrame, symbol: str | None = None) -> pd.DataFrame:
    """Detect close/KAMA crosses and KAMA slope changes."""

    _require_columns(frame, ["date", "close", "kama_10"], "kama")
    close = frame["close"].astype(float)
    kama = frame["kama_10"].astype(float)
    kama_slope = kama.diff()

    return _concat_events(
        [
            _events_from_mask(
                frame,
                symbol,
                family="kama",
                event_type="price_cross_up",
                mask=(close >= kama) & (close.shift(1) < kama.shift(1)),
                value=close,
                reference=kama,
            ),
            _events_from_mask(
                frame,
                symbol,
                family="kama",
                event_type="price_cross_down",
                mask=(close <= kama) & (close.shift(1) > kama.shift(1)),
                value=close,
                reference=kama,
            ),
            _events_from_mask(
                frame,
                symbol,
                family="kama",
                event_type="slope_turn_up",
                mask=(kama_slope > 0) & (kama_slope.shift(1) <= 0),
                value=kama,
                reference=kama.shift(1),
            ),
            _events_from_mask(
                frame,
                symbol,
                family="kama",
                event_type="slope_turn_down",
                mask=(kama_slope < 0) & (kama_slope.shift(1) >= 0),
                value=kama,
                reference=kama.shift(1),
            ),
        ]
    )


def detect_ichimoku_events(frame: pd.DataFrame, symbol: str | None = None) -> pd.DataFrame:
    """Detect Ichimoku conversion/base and cloud interactions."""

    _require_columns(
        frame,
        [
            "date",
            "close",
            "ichimoku_conversion",
            "ichimoku_base",
            "ichimoku_span_a",
            "ichimoku_span_b",
        ],
        "ichimoku",
    )
    close = frame["close"].astype(float)
    conversion = frame["ichimoku_conversion"].astype(float)
    base = frame["ichimoku_base"].astype(float)
    cloud_top = pd.concat(
        [frame["ichimoku_span_a"].astype(float), frame["ichimoku_span_b"].astype(float)],
        axis=1,
    ).max(axis=1)
    cloud_bottom = pd.concat(
        [frame["ichimoku_span_a"].astype(float), frame["ichimoku_span_b"].astype(float)],
        axis=1,
    ).min(axis=1)

    return _concat_events(
        [
            _events_from_mask(
                frame,
                symbol,
                family="ichimoku",
                event_type="conversion_cross_above_base",
                mask=(conversion >= base) & (conversion.shift(1) < base.shift(1)),
                value=conversion,
                reference=base,
            ),
            _events_from_mask(
                frame,
                symbol,
                family="ichimoku",
                event_type="conversion_cross_below_base",
                mask=(conversion <= base) & (conversion.shift(1) > base.shift(1)),
                value=conversion,
                reference=base,
            ),
            _events_from_mask(
                frame,
                symbol,
                family="ichimoku",
                event_type="price_breaks_above_cloud",
                mask=(close > cloud_top) & (close.shift(1) <= cloud_top.shift(1)),
                value=close,
                reference=cloud_top,
            ),
            _events_from_mask(
                frame,
                symbol,
                family="ichimoku",
                event_type="price_breaks_below_cloud",
                mask=(close < cloud_bottom) & (close.shift(1) >= cloud_bottom.shift(1)),
                value=close,
                reference=cloud_bottom,
            ),
        ]
    )


def detect_support_resistance_events(
    frame: pd.DataFrame,
    symbol: str | None = None,
    tolerance: float = 0.005,
) -> pd.DataFrame:
    """Detect support/resistance touches within a relative tolerance."""

    _require_columns(frame, ["date", "close", "support", "resistance"], "support_resistance")
    close = frame["close"].astype(float)
    support = frame["support"].astype(float)
    resistance = frame["resistance"].astype(float)
    support_distance = ((close - support) / close).abs()
    resistance_distance = ((resistance - close) / close).abs()

    return _concat_events(
        [
            _events_from_mask(
                frame,
                symbol,
                family="support_resistance",
                event_type="support_touch",
                mask=support_distance <= tolerance,
                value=close,
                reference=support,
            ),
            _events_from_mask(
                frame,
                symbol,
                family="support_resistance",
                event_type="resistance_touch",
                mask=resistance_distance <= tolerance,
                value=close,
                reference=resistance,
            ),
        ]
    )


def empty_events_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(EVENT_COLUMNS))


def _require_columns(frame: pd.DataFrame, columns: list[str], detector: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise EventDetectionError(
            f"{detector} detector missing required columns: {', '.join(missing)}"
        )


def _events_from_mask(
    frame: pd.DataFrame,
    symbol: str | None,
    family: str,
    event_type: str,
    mask: pd.Series,
    value: pd.Series,
    reference: pd.Series,
) -> pd.DataFrame:
    try:
        selected = frame.loc[mask.fillna(False)].copy()
        if selected.empty:
            return empty_events_frame()

        event_symbol = symbol or _symbol_from_frame(frame)
        events = pd.DataFrame(
            {
                "symbol": event_symbol,
                "event_family": family,
                "event_type": event_type,
                "event_date": selected["date"].astype(str),
                "value": value.loc[selected.index].astype(float).round(6),
                "reference": reference.loc[selected.index].astype(float).round(6),
            }
        )
        events["known_at"] = events["event_date"].map(_known_at_from_date)
        events["details"] = "known_after_daily_close"
        return events.loc[:, list(EVENT_COLUMNS)]
    except Exception as exc:
        raise EventDetectionError(f"{family}.{event_type} failed: {exc}") from exc


def _concat_events(event_frames: list[pd.DataFrame]) -> pd.DataFrame:
    non_empty = [frame for frame in event_frames if not frame.empty]
    if not non_empty:
        return empty_events_frame()
    return pd.concat(non_empty, ignore_index=True).loc[:, list(EVENT_COLUMNS)]


def _symbol_from_frame(frame: pd.DataFrame) -> str:
    if "symbol" not in frame.columns or frame["symbol"].dropna().empty:
        return "UNKNOWN"
    return str(frame["symbol"].dropna().iloc[0])


def _known_at_from_date(value: str) -> str:
    try:
        event_date = pd.to_datetime(value, errors="raise").date().isoformat()
    except Exception as exc:
        raise EventDetectionError(f"invalid event date {value!r}: {exc}") from exc
    return f"{event_date}T18:10:00+03:00"
