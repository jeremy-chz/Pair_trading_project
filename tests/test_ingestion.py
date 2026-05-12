"""
tests/test_ingestion.py
───────────────────────
Tests unitaires pour src/ingestion/get_data.py

Lance avec : pytest tests/
"""

import pandas as pd
import pytest
from src.ingestion.get_data import _clean_dtypes, COLUMNS


def make_raw_candle(open_time_ms: int = 1514764800000) -> list:
    """Génère une bougie brute au format Binance (liste de 12 éléments)."""
    return [
        open_time_ms,       # Open time (ms)
        "16500.00",         # Open
        "16800.00",         # High
        "16400.00",         # Low
        "16750.00",         # Close
        "1234.567",         # Volume
        open_time_ms + 899999,  # Close time (ms) = 15min - 1ms
        "20000000.00",      # Quote asset volume
        1500,               # Number of trades
        "600.00",           # Taker buy base
        "10000000.00",      # Taker buy quote
        "0",                # Ignore
    ]


class TestCleanDtypes:
    def test_open_time_is_utc_datetime(self):
        df = pd.DataFrame([make_raw_candle()], columns=COLUMNS)
        df = _clean_dtypes(df)
        assert df["Open time"].dt.tz is not None
        assert str(df["Open time"].dt.tz) == "UTC"

    def test_close_is_float(self):
        df = pd.DataFrame([make_raw_candle()], columns=COLUMNS)
        df = _clean_dtypes(df)
        assert df["Close"].dtype == float

    def test_number_of_trades_is_int(self):
        df = pd.DataFrame([make_raw_candle()], columns=COLUMNS)
        df = _clean_dtypes(df)
        assert df["Number of trades"].dtype == int

    def test_multiple_candles(self):
        candles = [make_raw_candle(1514764800000 + i * 900000) for i in range(10)]
        df = pd.DataFrame(candles, columns=COLUMNS)
        df = _clean_dtypes(df)
        assert len(df) == 10
        assert df["Open time"].is_monotonic_increasing
