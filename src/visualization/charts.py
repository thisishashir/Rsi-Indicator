"""Interactive Plotly charts kept separate from the Streamlit UI."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def price_chart(data, ticker: str) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(go.Candlestick(x=data.index, open=data["Open"], high=data["High"],
                                    low=data["Low"], close=data["Close"], name="OHLC"))
    for column, name, color in (("lower_band", "Lower band", "#8aa0b8"),
                                ("middle_band", "Middle band", "#d4a72c"),
                                ("upper_band", "Upper band", "#8aa0b8")):
        if column in data:
            figure.add_trace(go.Scatter(x=data.index, y=data[column], name=name,
                                        line={"color": color, "width": 1}))
    for column, name, color in (("sma_short", "Short SMA", "#19c3b1"), ("sma_long", "Long SMA", "#ef8354")):
        if column in data:
            figure.add_trace(go.Scatter(x=data.index, y=data[column], name=name,
                                        line={"color": color, "width": 1.5}))
    entries = data[data.get("entry_signal", False)]
    exits = data[data.get("exit_signal", False)]
    figure.add_trace(go.Scatter(x=entries.index, y=entries["Close"], mode="markers", name="Entry",
                                marker={"symbol": "triangle-up", "size": 10, "color": "#35d07f"}))
    figure.add_trace(go.Scatter(x=exits.index, y=exits["Close"], mode="markers", name="Exit",
                                marker={"symbol": "triangle-down", "size": 10, "color": "#f45b69"}))
    figure.update_layout(title=f"{ticker} price and indicators", xaxis_title="Date", yaxis_title="Price",
                         template="plotly_dark", height=580, xaxis_rangeslider_visible=False)
    return figure


def rsi_chart(data) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=data.index, y=data["rsi"], name="RSI", line={"color": "#f2c14e"}))
    figure.add_hrect(y0=0, y1=30, fillcolor="#35d07f", opacity=0.08, line_width=0)
    figure.add_hrect(y0=70, y1=100, fillcolor="#f45b69", opacity=0.08, line_width=0)
    figure.add_hline(y=30, line_dash="dot", line_color="#35d07f")
    figure.add_hline(y=70, line_dash="dot", line_color="#f45b69")
    figure.update_layout(title="Relative Strength Index", yaxis_title="RSI", yaxis_range=[0, 100],
                         template="plotly_dark", height=260)
    return figure


def equity_chart(data) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=data.index, y=data["portfolio_value"], name="Strategy", line={"color": "#19c3b1"}))
    figure.add_trace(go.Scatter(x=data.index, y=data["buy_hold_value"], name="Buy and hold", line={"color": "#ef8354"}))
    figure.update_layout(title="Strategy versus buy-and-hold equity", yaxis_title="Portfolio value",
                         template="plotly_dark", height=360)
    return figure


def drawdown_chart(data) -> go.Figure:
    figure = go.Figure(go.Scatter(x=data.index, y=data["drawdown"] * 100, name="Drawdown",
                                  fill="tozeroy", line={"color": "#f45b69"}))
    figure.update_layout(title="Strategy drawdown", yaxis_title="Drawdown (%)", template="plotly_dark", height=280)
    return figure