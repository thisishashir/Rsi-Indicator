import pandas as pd

from src.backtesting.engine import BacktestConfig, run_backtest


def test_next_bar_execution_and_costs():
    data = pd.DataFrame({"Close": [100, 110, 110, 100], "position": [1, 1, 0, 0]},
                        index=pd.date_range("2020-01-01", periods=4))
    result = run_backtest(data, BacktestConfig(initial_capital=1000, transaction_cost=0.01))
    assert result.data.loc[result.data.index[0], "held_position"] == 0
    assert result.data.loc[result.data.index[1], "held_position"] == 1
    assert len(result.trades) == 1
    assert result.trades.iloc[0]["entry_price"] == 110


def test_empty_data_rejected():
    try:
        run_backtest(pd.DataFrame(columns=["Close", "position"]))
    except ValueError:
        pass
    else:
        raise AssertionError("empty data should fail")