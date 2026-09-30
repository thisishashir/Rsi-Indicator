"""Performance statistics for strategy and benchmark equity series."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def maximum_drawdown(equity: pd.Series) -> tuple[pd.Series, float]:
    """Return drawdown series and its worst value."""
    peak = equity.cummax()
    drawdown = equity / peak.replace(0, np.nan) - 1
    return drawdown, float(drawdown.min()) if not drawdown.empty else 0.0


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods: int = 252) -> float:
    """Return annualized excess-return Sharpe estimate, or zero if undefined."""
    if periods <= 0:
        raise ValueError("periods must be positive")
    daily_rf = (1 + risk_free_rate) ** (1 / periods) - 1
    excess = returns.dropna() - daily_rf
    deviation = excess.std(ddof=1)
    if excess.empty or deviation == 0 or pd.isna(deviation):
        return 0.0
    return float(excess.mean() / deviation * math.sqrt(periods))


def calculate_metrics(
    equity_data: pd.DataFrame,
    trades: pd.DataFrame,
    initial_capital: float,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> dict[str, float | int]:
    """Calculate strategy, benchmark, risk, and trade statistics."""
    if equity_data.empty:
        return {}
    equity = equity_data["portfolio_value"]
    returns = equity_data["strategy_return"].fillna(0)
    final_value = float(equity.iloc[-1])
    total_return = final_value / initial_capital - 1
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1 / periods_per_year)
    drawdown, max_dd = maximum_drawdown(equity)
    closed = trades["net_return"].dropna() if not trades.empty else pd.Series(dtype=float)
    wins = closed[closed > 0]
    losses = closed[closed <= 0]
    benchmark_return = float(equity_data["buy_hold_value"].iloc[-1] / initial_capital - 1)
    exposure = float(equity_data["held_position"].mean())
    return {
        "initial_capital": float(initial_capital), "final_capital": final_value,
        "total_return": float(total_return), "cagr": float((1 + total_return) ** (1 / years) - 1),
        "volatility": float(returns.std(ddof=1) * math.sqrt(periods_per_year)) if len(returns) > 1 else 0.0,
        "sharpe_ratio": sharpe_ratio(returns, risk_free_rate, periods_per_year),
        "max_drawdown": max_dd, "win_rate": float(len(wins) / len(closed)) if len(closed) else 0.0,
        "total_trades": int(len(closed)), "winning_trades": int(len(wins)),
        "losing_trades": int(len(losses)), "average_trade": float(closed.mean()) if len(closed) else 0.0,
        "average_winning_trade": float(wins.mean()) if len(wins) else 0.0,
        "average_losing_trade": float(losses.mean()) if len(losses) else 0.0,
        "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() else 0.0,
        "best_trade": float(closed.max()) if len(closed) else 0.0,
        "worst_trade": float(closed.min()) if len(closed) else 0.0,
        "exposure": exposure, "buy_hold_return": benchmark_return,
        "maximum_drawdown": max_dd, "drawdown_current": float(drawdown.iloc[-1]),
    }