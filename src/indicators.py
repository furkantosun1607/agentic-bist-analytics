"""Deterministic technical indicator calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""

    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential moving average."""

    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def kama(
    series: pd.Series,
    window: int = 10,
    fast: int = 2,
    slow: int = 30,
) -> pd.Series:
    """Kaufman's Adaptive Moving Average."""

    values = series.astype(float)
    change = values.diff(window).abs()
    volatility = values.diff().abs().rolling(window=window, min_periods=window).sum()
    efficiency_ratio = (change / volatility).replace([np.inf, -np.inf], 0).fillna(0)
    fast_sc = 2 / (fast + 1)
    slow_sc = 2 / (slow + 1)
    smoothing_constant = (efficiency_ratio * (fast_sc - slow_sc) + slow_sc) ** 2

    result = pd.Series(np.nan, index=values.index, dtype="float64")
    if len(values) <= window:
        return result

    first_valid = window
    result.iloc[first_valid] = values.iloc[first_valid]
    for index in range(first_valid + 1, len(values)):
        previous = result.iloc[index - 1]
        result.iloc[index] = previous + smoothing_constant.iloc[index] * (
            values.iloc[index] - previous
        )

    return result


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder-style exponential smoothing."""

    delta = series.astype(float).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    relative_strength = avg_gain / avg_loss
    result = 100 - (100 / (1 + relative_strength))
    return result.where(avg_loss != 0, 100)


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Moving Average Convergence/Divergence."""

    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {
            "macd": macd_line,
            "macd_signal": signal_line,
            "macd_histogram": histogram,
        },
        index=series.index,
    )


def bollinger_bands(
    series: pd.Series,
    window: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    """Bollinger Bands."""

    middle = sma(series, window)
    rolling_std = series.rolling(window=window, min_periods=window).std()
    upper = middle + (rolling_std * num_std)
    lower = middle - (rolling_std * num_std)
    width = (upper - lower) / middle
    return pd.DataFrame(
        {
            "bb_lower": lower,
            "bb_middle": middle,
            "bb_upper": upper,
            "bb_width": width,
        },
        index=series.index,
    )


def true_range(prices: pd.DataFrame) -> pd.Series:
    """True range for OHLC data."""

    high = prices["high"].astype(float)
    low = prices["low"].astype(float)
    close = prices["close"].astype(float)
    previous_close = close.shift(1)
    ranges = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def atr(prices: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average True Range."""

    return true_range(prices).rolling(window=window, min_periods=window).mean()


def supertrend(
    prices: pd.DataFrame,
    window: int = 10,
    multiplier: float = 3.0,
) -> pd.DataFrame:
    """Supertrend bands and direction."""

    high = prices["high"].astype(float)
    low = prices["low"].astype(float)
    close = prices["close"].astype(float)
    hl2 = (high + low) / 2
    atr_values = atr(prices, window)
    basic_upper = hl2 + (multiplier * atr_values)
    basic_lower = hl2 - (multiplier * atr_values)

    final_upper = pd.Series(np.nan, index=prices.index, dtype="float64")
    final_lower = pd.Series(np.nan, index=prices.index, dtype="float64")
    direction = pd.Series(np.nan, index=prices.index, dtype="float64")
    trend = pd.Series(np.nan, index=prices.index, dtype="float64")

    for index in range(len(prices)):
        if pd.isna(atr_values.iloc[index]):
            continue

        if index == 0 or pd.isna(final_upper.iloc[index - 1]):
            final_upper.iloc[index] = basic_upper.iloc[index]
            final_lower.iloc[index] = basic_lower.iloc[index]
            direction.iloc[index] = 1.0
        else:
            previous_close = close.iloc[index - 1]
            previous_upper = final_upper.iloc[index - 1]
            previous_lower = final_lower.iloc[index - 1]

            final_upper.iloc[index] = (
                basic_upper.iloc[index]
                if basic_upper.iloc[index] < previous_upper or previous_close > previous_upper
                else previous_upper
            )
            final_lower.iloc[index] = (
                basic_lower.iloc[index]
                if basic_lower.iloc[index] > previous_lower or previous_close < previous_lower
                else previous_lower
            )

            if close.iloc[index] > previous_upper:
                direction.iloc[index] = 1.0
            elif close.iloc[index] < previous_lower:
                direction.iloc[index] = -1.0
            else:
                direction.iloc[index] = direction.iloc[index - 1]

        trend.iloc[index] = (
            final_lower.iloc[index] if direction.iloc[index] == 1.0 else final_upper.iloc[index]
        )

    return pd.DataFrame(
        {
            "supertrend": trend,
            "supertrend_direction": direction,
            "supertrend_upper": final_upper,
            "supertrend_lower": final_lower,
        },
        index=prices.index,
    )


def ichimoku(
    prices: pd.DataFrame,
    conversion_window: int = 9,
    base_window: int = 26,
    span_b_window: int = 52,
    displacement: int = 26,
) -> pd.DataFrame:
    """Ichimoku Cloud components."""

    high = prices["high"].astype(float)
    low = prices["low"].astype(float)
    conversion = _midpoint(high, low, conversion_window)
    base = _midpoint(high, low, base_window)
    span_a = ((conversion + base) / 2).shift(displacement)
    span_b = _midpoint(high, low, span_b_window).shift(displacement)
    lagging = prices["close"].astype(float).shift(-displacement)

    return pd.DataFrame(
        {
            "ichimoku_conversion": conversion,
            "ichimoku_base": base,
            "ichimoku_span_a": span_a,
            "ichimoku_span_b": span_b,
            "ichimoku_lagging": lagging,
        },
        index=prices.index,
    )


def support_resistance(prices: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Rolling support and resistance levels."""

    support = prices["low"].astype(float).rolling(window=window, min_periods=window).min()
    resistance = prices["high"].astype(float).rolling(window=window, min_periods=window).max()
    close = prices["close"].astype(float)
    support_distance = (close - support) / close
    resistance_distance = (resistance - close) / close
    return pd.DataFrame(
        {
            "support": support,
            "resistance": resistance,
            "support_distance": support_distance,
            "resistance_distance": resistance_distance,
        },
        index=prices.index,
    )


def volume_indicators(prices: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Basic volume moving average and relative volume."""

    volume = prices["volume"].astype(float)
    volume_sma = sma(volume, window)
    relative_volume = volume / volume_sma
    return pd.DataFrame(
        {
            "volume_sma": volume_sma,
            "relative_volume": relative_volume,
        },
        index=prices.index,
    )


def add_all_indicators(prices: pd.DataFrame) -> pd.DataFrame:
    """Append the core indicator set to normalized OHLCV prices."""

    result = prices.copy()
    close = result["close"].astype(float)

    indicator_frames = [
        pd.DataFrame(
            {
                "sma_20": sma(close, 20),
                "sma_50": sma(close, 50),
                "ema_20": ema(close, 20),
                "kama_10": kama(close, 10),
                "rsi_14": rsi(close, 14),
                "atr_14": atr(result, 14),
            },
            index=result.index,
        ),
        macd(close),
        bollinger_bands(close),
        supertrend(result),
        ichimoku(result),
        support_resistance(result),
        volume_indicators(result),
    ]

    return pd.concat([result, *indicator_frames], axis=1)


def _midpoint(high: pd.Series, low: pd.Series, window: int) -> pd.Series:
    rolling_high = high.rolling(window=window, min_periods=window).max()
    rolling_low = low.rolling(window=window, min_periods=window).min()
    return (rolling_high + rolling_low) / 2
