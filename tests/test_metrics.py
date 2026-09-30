import pandas as pd

from src.backtesting.metrics import calculate_metrics, maximum_drawdown, sharpe_ratio


def test_drawdown_and_zero_sharpe():
    equity = pd.Series([100.0, 120.0, 90.0, 100.0])
    drawdown, maximum = maximum_drawdown(equity)
    assert maximum == -0.25
    assert sharpe_ratio(pd.Series([0.0, 0.0])) == 0.0
    assert drawdown.iloc[2] == -0.25


def test_trade_metrics_handle_no_trades():
    index = pd.date_range("2020-01-01", periods=3)
    data = pd.DataFrame({"portfolio_value": [100, 100, 100], "strategy_return": [0, 0, 0],
                         "buy_hold_value": [100, 101, 102], "held_position": [0, 0, 0]}, index=index)
    metrics = calculate_metrics(data, pd.DataFrame(columns=["net_return"]), 100)
    assert metrics["total_trades"] == 0
    assert metrics["win_rate"] == 0