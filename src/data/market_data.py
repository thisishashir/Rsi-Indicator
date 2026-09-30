"""Yahoo Finance market-data access and validation."""

from __future__ import annotations

from datetime import date

import pandas as pd


class MarketDataError(ValueError):
    """Raised when market data cannot be downloaded or cleaned."""


def get_market_data(
    ticker: str,
    start_date: date | str,
    end_date: date | str,
    interval: str = "1d",
) -> pd.DataFrame:
    """Download and clean OHLCV data from Yahoo Finance.

    Yahoo's ``end`` date is exclusive. The returned frame is sorted, unique,
    and contains only rows with complete OHLCV values. No data is fabricated.
    """
    symbol = str(ticker).strip().upper()
    if not symbol or any(character in symbol for character in " \t\n"):
        raise MarketDataError("Ticker must be a non-empty symbol without whitespace.")

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if pd.isna(start) or pd.isna(end):
        raise MarketDataError("Start and end dates must be valid dates.")
    if start >= end:
        raise MarketDataError("Start date must be before end date.")

    try:
        import yfinance as yf

        data = yf.download(
            symbol,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval=interval,
            auto_adjust=False,
            progress=False,
            group_by="column",
        )
    except Exception as exc:  # network/provider errors should be shown to users
        raise MarketDataError(f"Unable to download {symbol}: {exc}") from exc

    if data is None or data.empty:
        raise MarketDataError(f"Yahoo Finance returned no data for {symbol}.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    expected = ["Open", "High", "Low", "Close", "Volume"]
    missing = [column for column in expected if column not in data.columns]
    if missing:
        raise MarketDataError(f"Downloaded data is missing columns: {', '.join(missing)}")

    cleaned = data.loc[:, expected].copy()
    cleaned.index = pd.to_datetime(cleaned.index)
    cleaned = cleaned[~cleaned.index.duplicated(keep="last")].sort_index()
    cleaned = cleaned.dropna(subset=expected)
    if cleaned.empty:
        raise MarketDataError("No complete OHLCV rows remain after cleaning.")
    return cleaned