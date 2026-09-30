"""A transparent long-only backtesting engine."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: float = 100_000.0
    transaction_cost: float = 0.001
    slippage: float = 0.0
    allocation: float = 1.0

    def __post_init__(self) -> None:
        if self.initial_capital <= 0 or self.transaction_cost < 0 or self.slippage < 0:
            raise ValueError("Capital must be positive and costs cannot be negative")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")


@dataclass
class BacktestResult:
    data: pd.DataFrame
    trades: pd.DataFrame
    initial_capital: float


def run_backtest(price_data: pd.DataFrame, config: BacktestConfig | None = None) -> BacktestResult:
    """Run signals with next-bar execution and proportional costs.

    A signal observed at close[t] becomes the held position for bar t+1.
    This makes the close used by the indicator unavailable to the same return.
    """
    config = config or BacktestConfig()
    required = {"Close", "position"}
    missing = required.difference(price_data.columns)
    if missing:
        raise ValueError(f"Backtest data missing: {', '.join(sorted(missing))}")
    if price_data.empty:
        raise ValueError("Cannot backtest an empty data set")

    result = price_data.copy().sort_index()
    desired_position = result["position"].astype(float).clip(0, 1)
    held_position = desired_position.shift(1).fillna(0.0)
    close_return = result["Close"].pct_change().fillna(0.0)
    turnover = held_position.diff().abs().fillna(held_position)
    cost_rate = config.transaction_cost + config.slippage
    strategy_return = held_position * close_return - turnover * cost_rate
    result["market_return"] = close_return
    result["held_position"] = held_position
    result["turnover"] = turnover
    result["strategy_return"] = strategy_return
    result["portfolio_value"] = config.initial_capital * (1 + strategy_return).cumprod()
    result["cash"] = result["portfolio_value"] * (1 - held_position * config.allocation)
    result["equity_curve"] = result["portfolio_value"]
    result["buy_hold_value"] = config.initial_capital * (1 + close_return).cumprod()
    result["drawdown"] = result["portfolio_value"] / result["portfolio_value"].cummax() - 1

    trades: list[dict[str, object]] = []
    open_trade: dict[str, object] | None = None
    for timestamp, row in result.iterrows():
        previous = result.loc[timestamp, "held_position"]
        if previous == 1 and open_trade is None:
            open_trade = {"entry_date": timestamp, "entry_price": float(row["Close"])}
        if previous == 0 and open_trade is not None:
            entry_price = float(open_trade["entry_price"])
            exit_price = float(row["Close"])
            gross_return = exit_price / entry_price - 1
            net_return = gross_return - 2 * cost_rate
            trades.append({**open_trade, "exit_date": timestamp, "exit_price": exit_price,
                           "gross_return": gross_return, "net_return": net_return,
                           "pnl": config.initial_capital * config.allocation * net_return,
                           "costs": 2 * config.initial_capital * config.allocation * cost_rate,
                           "holding_period": (timestamp - open_trade["entry_date"]).days})
            open_trade = None
    trade_frame = pd.DataFrame(trades, columns=[
        "entry_date", "entry_price", "exit_date", "exit_price", "gross_return",
        "net_return", "pnl", "costs", "holding_period"
    ])
    return BacktestResult(result, trade_frame, config.initial_capital)