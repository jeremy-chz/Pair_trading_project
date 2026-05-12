"""
tests/test_cleaning.py
──────────────────────
Tests unitaires pour src/processing/cleaning.py

Lance avec : pytest tests/
"""

import pandas as pd
import pytest
from src.processing.cleaning import align_pairs, detect_gaps


def make_ohlcv(timestamps: list) -> pd.DataFrame:
    """Crée un DataFrame OHLCV minimal avec les timestamps donnés."""
    index = pd.DatetimeIndex(timestamps, tz="UTC", name="Open time")
    return pd.DataFrame({"Close": range(len(timestamps))}, index=index)


class TestAlignPairs:
    def test_same_index_no_loss(self):
        ts = pd.date_range("2024-01-01", periods=100, freq="15min", tz="UTC")
        df_a = make_ohlcv(ts)
        df_b = make_ohlcv(ts)
        a_aligned, b_aligned = align_pairs(df_a, df_b)
        assert len(a_aligned) == 100
        assert len(b_aligned) == 100

    def test_missing_timestamps_removed(self):
        ts_full = pd.date_range("2024-01-01", periods=10, freq="15min", tz="UTC")
        ts_partial = ts_full[[0, 1, 2, 5, 6, 7, 8, 9]]  # trous aux indices 3 et 4
        df_a = make_ohlcv(ts_full)
        df_b = make_ohlcv(ts_partial)
        a_aligned, b_aligned = align_pairs(df_a, df_b)
        assert len(a_aligned) == len(ts_partial)
        assert len(b_aligned) == len(ts_partial)

    def test_aligned_indexes_are_equal(self):
        ts_a = pd.date_range("2024-01-01", periods=10, freq="15min", tz="UTC")
        ts_b = ts_a[[0, 2, 4, 6, 8]]
        df_a = make_ohlcv(ts_a)
        df_b = make_ohlcv(ts_b)
        a_aligned, b_aligned = align_pairs(df_a, df_b)
        assert a_aligned.index.equals(b_aligned.index)


class TestDetectGaps:
    def test_no_gaps(self):
        ts = pd.date_range("2024-01-01", periods=50, freq="15min", tz="UTC")
        df = make_ohlcv(ts)
        gaps = detect_gaps(df, timeframe_minutes=15)
        assert gaps.empty

    def test_detects_one_gap(self):
        ts_list = list(pd.date_range("2024-01-01", periods=5, freq="15min", tz="UTC"))
        # Insérer un trou de 2h entre la 3e et la 4e bougie
        ts_list[3] = ts_list[2] + pd.Timedelta(hours=2)
        ts_list[4] = ts_list[3] + pd.Timedelta(minutes=15)
        df = make_ohlcv(ts_list)
        gaps = detect_gaps(df, timeframe_minutes=15)
        assert len(gaps) == 1
