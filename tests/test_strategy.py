import numpy as np
import pandas as pd

from src.indicators.technical_indicators import add_indicators
from src.strategy.signals import StrategyConfig, generate_signals


def test_strategy_position_does_not_reenter_while_long():
    prices = pd.DataFrame({"Close": np.linspace(100, 110, 80), "Open": np.linspace(100, 110, 80),
                           "High": np.linspace(101, 111, 80), "Low": np.linspace(99, 109, 80), "Volume": 1},
                          index=pd.date_range("2020-01-01", periods=80))
    indicators = add_indicators(prices, 5, 5, 2, 3, 8)
    signals = generate_signals(indicators, StrategyConfig(use_rsi=False, use_bollinger=False, use_trend_filter=True))
    assert signals["position"].isin([0, 1]).all()
    assert not ((signals["signal"] == 1) & (signals["position"].shift(1) == 1)).any()


def test_invalid_strategy_config():
    try:
        StrategyConfig(rsi_oversold=80, rsi_overbought=70)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid RSI thresholds should fail")