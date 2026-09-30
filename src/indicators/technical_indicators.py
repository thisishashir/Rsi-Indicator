"""Technical indicators implemented with pandas rolling operations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _validate_period(period: int) -> None:
    if not isinstance(period, int) or period <= 0:
        raise ValueError("period must be a positive integer")


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Wilder RSI from price changes without look-ahead data."""
    _validate_period(period)
    delta = close.astype(float).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    average_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    average_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    relative_strength = average_gain / average_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + relative_strength))
    rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100)
    rsi = rsi.mask((average_gain == 0) & (average_loss > 0), 0)
    return rsi.rename("rsi")


def calculate_bollinger_bands(
    close: pd.Series, period: int = 20, std_dev: float = 2.0
) -> pd.DataFrame:
    """Return middle, upper, lower, width, and percent-B bands."""
    _validate_period(period)
    if std_dev <= 0:
        raise ValueError("std_dev must be positive")
    middle = close.astype(float).rolling(period, min_periods=period).mean()
    deviation = close.astype(float).rolling(period, min_periods=period).std(ddof=0)
    upper = middle + std_dev * deviation
    lower = middle - std_dev * deviation
    width = (upper - lower) / middle.replace(0, np.nan)
    percent_b = (close - lower) / (upper - lower).replace(0, np.nan)
    return pd.DataFrame(
        {"middle_band": middle, "upper_band": upper, "lower_band": lower,
         "band_width": width, "percent_b": percent_b}, index=close.index
    )


def calculate_sma(close: pd.Series, period: int) -> pd.Series:
    """Calculate a simple moving average."""
    _validate_period(period)
    return close.astype(float).rolling(period, min_periods=period).mean().rename(f"sma_{period}")


def calculate_ema(close: pd.Series, period: int) -> pd.Series:
    """Calculate an exponentially weighted moving average."""
    _validate_period(period)
    return close.astype(float).ewm(span=period, min_periods=period, adjust=False).mean().rename(f"ema_{period}")


def add_indicators(
    data: pd.DataFrame,
    rsi_period: int = 14,
    bollinger_period: int = 20,
    bollinger_std: float = 2.0,
    short_ma_period: int = 20,
    long_ma_period: int = 50,
) -> pd.DataFrame:
    """Add all supported indicators to an OHLCV frame."""
    if "Close" not in data:
        raise ValueError("Data must contain a Close column")
    result = data.copy()
    result["rsi"] = calculate_rsi(result["Close"], rsi_period)
    bands = calculate_bollinger_bands(result["Close"], bollinger_period, bollinger_std)
    result = result.join(bands)
    result[f"sma_{short_ma_period}"] = calculate_sma(result["Close"], short_ma_period)
    result[f"sma_{long_ma_period}"] = calculate_sma(result["Close"], long_ma_period)
    result[f"ema_{short_ma_period}"] = calculate_ema(result["Close"], short_ma_period)
    result[f"ema_{long_ma_period}"] = calculate_ema(result["Close"], long_ma_period)
    short_ma = result[f"sma_{short_ma_period}"]
    long_ma = result[f"sma_{long_ma_period}"]
    result["ma_bullish"] = short_ma >= long_ma
    result["ma_cross_up"] = (short_ma >= long_ma) & (short_ma.shift(1) < long_ma.shift(1))
    result["ma_cross_down"] = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
    return result