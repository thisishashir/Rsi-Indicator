import numpy as np
import pandas as pd

from src.indicators.technical_indicators import calculate_bollinger_bands, calculate_ema, calculate_rsi, calculate_sma


def test_moving_averages_and_bollinger_values():
    close = pd.Series([1, 2, 3, 4, 5], dtype=float)
    assert calculate_sma(close, 3).iloc[-1] == 4
    assert calculate_ema(close, 3).notna().sum() == 3
    bands = calculate_bollinger_bands(close, 3, 2)
    assert bands.loc[4, "middle_band"] == 4
    assert bands.loc[4, "upper_band"] > bands.loc[4, "middle_band"]


def test_rsi_bounds_and_direction():
    rising = pd.Series(np.arange(30, dtype=float))
    rsi = calculate_rsi(rising, 14)
    assert rsi.dropna().iloc[-1] == 100
    assert ((rsi.dropna() >= 0) & (rsi.dropna() <= 100)).all()