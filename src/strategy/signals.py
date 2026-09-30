"""Deterministic long-only signal state machine."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class StrategyConfig:
    """Parameters and feature switches for the default mean-reversion strategy."""

    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    use_rsi: bool = True
    use_bollinger: bool = True
    use_trend_filter: bool = True
    exit_logic: str = "any"

    def __post_init__(self) -> None:
        if not 0 <= self.rsi_oversold <= 100 or not 0 <= self.rsi_overbought <= 100:
            raise ValueError("RSI thresholds must be between 0 and 100")
        if self.rsi_oversold >= self.rsi_overbought:
            raise ValueError("RSI oversold must be below overbought")
        if self.exit_logic not in {"any", "all"}:
            raise ValueError("exit_logic must be 'any' or 'all'")


def _combined(conditions: list[pd.Series], index: pd.Index, mode: str) -> pd.Series:
    if not conditions:
        return pd.Series(False, index=index, dtype=bool)
    frame = pd.concat(conditions, axis=1).fillna(False)
    return frame.any(axis=1) if mode == "any" else frame.all(axis=1)


def generate_signals(data: pd.DataFrame, config: StrategyConfig | None = None) -> pd.DataFrame:
    """Generate entry/exit events and a non-repeating position state."""
    config = config or StrategyConfig()
    required = {"Close", "rsi", "lower_band", "upper_band", "ma_bullish", "ma_cross_down"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Indicator columns missing: {', '.join(sorted(missing))}")

    entry_conditions: list[pd.Series] = []
    if config.use_rsi:
        entry_conditions.append(data["rsi"] < config.rsi_oversold)
    if config.use_bollinger:
        entry_conditions.append(data["Close"] <= data["lower_band"])
    if config.use_trend_filter:
        entry_conditions.append(data["ma_bullish"])
    entry_signal = _combined(entry_conditions, data.index, "all")

    exit_conditions: list[pd.Series] = []
    if config.use_rsi:
        exit_conditions.append(data["rsi"] > config.rsi_overbought)
    if config.use_bollinger:
        exit_conditions.append(data["Close"] >= data["upper_band"])
    if config.use_trend_filter:
        exit_conditions.append(data["ma_cross_down"])
    exit_signal = _combined(exit_conditions, data.index, config.exit_logic)

    position = []
    state = 0
    for enter, leave in zip(entry_signal, exit_signal):
        if state == 0 and enter:
            state = 1
        elif state == 1 and leave:
            state = 0
        position.append(state)

    result = data.copy()
    result["entry_signal"] = entry_signal.astype(bool)
    result["exit_signal"] = exit_signal.astype(bool)
    result["position"] = pd.Series(position, index=data.index, dtype=int)
    result["signal"] = result["position"].diff().fillna(result["position"]).astype(int)
    return result