"""Streamlit entry point for the quantitative strategy analyzer."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.backtesting.engine import BacktestConfig, run_backtest
from src.backtesting.metrics import calculate_metrics
from src.data.market_data import MarketDataError, get_market_data
from src.indicators.technical_indicators import add_indicators
from src.strategy.signals import StrategyConfig, generate_signals
from src.visualization.charts import drawdown_chart, equity_chart, price_chart, rsi_chart


st.set_page_config(page_title="Quant Strategy Analyzer", page_icon="Q", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; }
[data-testid="stMetricValue"] { color: #19c3b1; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def cached_market_data(ticker: str, start: date, end: date, interval: str) -> pd.DataFrame:
    """Cache network results; downstream calculations remain parameter-sensitive."""
    return get_market_data(ticker, start, end, interval)


def format_percent(value: float) -> str:
    return f"{value:.2%}"


def analyze_ticker(ticker: str, settings: dict) -> tuple[pd.DataFrame, object, dict]:
    raw = cached_market_data(ticker, settings["start"], settings["end"], settings["interval"])
    indicators = add_indicators(raw, settings["rsi_period"], settings["bb_period"], settings["bb_std"],
                                 settings["short_ma"], settings["long_ma"])
    indicators = indicators.rename(columns={f"sma_{settings['short_ma']}": "sma_short",
                                            f"sma_{settings['long_ma']}": "sma_long"})
    signals = generate_signals(indicators, StrategyConfig(settings["rsi_oversold"], settings["rsi_overbought"],
                                                           settings["use_rsi"], settings["use_bb"],
                                                           settings["use_trend"], settings["exit_logic"]))
    backtest = run_backtest(signals, BacktestConfig(settings["capital"], settings["cost"], settings["slippage"], settings["allocation"]))
    metrics = calculate_metrics(backtest.data, backtest.trades, backtest.initial_capital, settings["risk_free"])
    return backtest.data, backtest, metrics


def sidebar_settings() -> tuple[list[str], dict]:
    with st.sidebar:
        st.header("Research controls")
        tickers = [item.strip().upper() for item in st.text_area("Tickers", "SPY\nQQQ", height=80).splitlines() if item.strip()]
        today = date.today()
        start, end = st.date_input("Historical range", (today - timedelta(days=365 * 5), today))
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"])
        st.subheader("Capital and costs")
        capital = st.number_input("Initial capital", min_value=100.0, value=100000.0, step=1000.0)
        allocation = st.slider("Capital allocation", 0.05, 1.0, 1.0, 0.05)
        cost = st.number_input("Transaction cost rate", min_value=0.0, value=0.001, format="%.4f")
        slippage = st.number_input("Slippage rate", min_value=0.0, value=0.0, format="%.4f")
        risk_free = st.number_input("Annual risk-free rate", value=0.0, format="%.4f")
        st.subheader("Indicators")
        rsi_period = st.number_input("RSI period", 2, 100, 14)
        rsi_oversold = st.slider("RSI oversold", 1, 49, 30)
        rsi_overbought = st.slider("RSI overbought", 51, 99, 70)
        bb_period = st.number_input("Bollinger period", 2, 200, 20)
        bb_std = st.number_input("Bollinger standard deviations", 0.1, 5.0, 2.0, 0.1)
        short_ma = st.number_input("Short SMA", 2, 200, 20)
        long_ma = st.number_input("Long SMA", 3, 500, 50)
        st.subheader("Signal components")
        use_rsi = st.checkbox("Use RSI", True)
        use_bb = st.checkbox("Use Bollinger Bands", True)
        use_trend = st.checkbox("Use MA trend filter", True)
        exit_logic = st.radio("Exit combination", ["any", "all"], horizontal=True)
    return tickers, locals()


def show_result(ticker: str, data: pd.DataFrame, backtest, metrics: dict) -> None:
    st.subheader(ticker)
    cards = [("Final capital", f"${metrics['final_capital']:,.0f}"), ("Total return", format_percent(metrics["total_return"])),
             ("CAGR", format_percent(metrics["cagr"])), ("Sharpe estimate", f"{metrics['sharpe_ratio']:.2f}"),
             ("Max drawdown", format_percent(metrics["max_drawdown"])), ("Win rate", format_percent(metrics["win_rate"])),
             ("Closed trades", str(metrics["total_trades"])), ("Buy and hold", format_percent(metrics["buy_hold_return"]))]
    columns = st.columns(len(cards))
    for column, (label, value) in zip(columns, cards):
        column.metric(label, value)
    st.plotly_chart(price_chart(data, ticker), use_container_width=True)
    st.plotly_chart(rsi_chart(data), use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(equity_chart(data), use_container_width=True)
    with right:
        st.plotly_chart(drawdown_chart(data), use_container_width=True)
    st.download_button("Download trade ledger", backtest.trades.to_csv(index=False), f"{ticker}_trades.csv", "text/csv")
    st.dataframe(backtest.trades, use_container_width=True)
    with st.expander("Raw OHLCV, indicators, signals, and returns"):
        st.download_button("Download analysis CSV", data.to_csv(), f"{ticker}_analysis.csv", "text/csv")
        st.dataframe(data, use_container_width=True)


def main() -> None:
    st.title("Quantitative Trading Strategy Analyzer")
    st.caption("Historical research and backtesting for configurable RSI, Bollinger, and moving-average signals. Past performance is not predictive.")
    tickers, settings = sidebar_settings()
    if not tickers:
        st.info("Enter at least one ticker in the sidebar.")
        return
    results = []
    for ticker in tickers:
        try:
            data, backtest, metrics = analyze_ticker(ticker, settings)
            results.append({"Ticker": ticker, "Total Return": metrics["total_return"], "CAGR": metrics["cagr"],
                            "Sharpe": metrics["sharpe_ratio"], "Max Drawdown": metrics["max_drawdown"],
                            "Win Rate": metrics["win_rate"], "Trades": metrics["total_trades"],
                            "Buy and Hold": metrics["buy_hold_return"]})
            show_result(ticker, data, backtest, metrics)
        except (MarketDataError, ValueError) as exc:
            st.error(f"{ticker}: {exc}")
    if len(results) > 1:
        st.header("Ticker comparison")
        st.dataframe(pd.DataFrame(results).style.format({column: "{:.2%}" for column in ["Total Return", "CAGR", "Max Drawdown", "Win Rate", "Buy and Hold"]}), use_container_width=True)


if __name__ == "__main__":
    main()