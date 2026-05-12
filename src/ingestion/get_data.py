"""
src/ingestion/get_data.py
─────────────────────────
Récupère les données OHLCV depuis Binance via ccxt.
Gère l'historique complet + les mises à jour incrémentales.

Usage :
    python src/ingestion/get_data.py --symbol BTC/USDT --timeframe 15m --start 2018-01-01
    python src/ingestion/get_data.py --symbol ETH/USDT --timeframe 1h  --start 2020-01-01
"""

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import ccxt
import pandas as pd

# ── Constantes ────────────────────────────────────────────────────────────────

COLUMNS = [
    "Open time", "Open", "High", "Low", "Close", "Volume",
    "Close time", "Quote asset volume", "Number of trades",
    "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore",
]

OUTPUT_DIR = Path("data/raw")


# ── Fonctions principales ─────────────────────────────────────────────────────

def fetch_all_ohlcv(
    symbol: str = "BTC/USDT",
    timeframe: str = "15m",
    start_date: str = "2018-01-01",
    sleep_seconds: float = 0.2,
) -> pd.DataFrame:
    """
    Récupère toutes les bougies depuis start_date jusqu'à maintenant.

    Args:
        symbol        : Paire Binance, ex : "BTC/USDT"
        timeframe     : Granularité, ex : "15m", "1h", "4h", "1d"
        start_date    : Date de début au format "YYYY-MM-DD"
        sleep_seconds : Pause entre requêtes (évite le rate limit)

    Returns:
        DataFrame avec colonnes OHLCV, index non-réinitialisé.
    """
    exchange = ccxt.binance()
    current_start = int(pd.Timestamp(start_date, tz="UTC").timestamp() * 1000)
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    all_candles = []

    print(f"Récupération {symbol} [{timeframe}] depuis {start_date}...")

    while current_start < now:
        dt_str = pd.to_datetime(current_start, unit="ms")
        print(f"  → {dt_str}", end="\r")

        params = {
            "symbol": symbol.replace("/", ""),
            "interval": timeframe,
            "startTime": current_start,
            "limit": 1000,
        }

        batch = exchange.public_get_klines(params)

        if not batch:
            break

        all_candles.extend(batch)
        current_start = int(batch[-1][0]) + 1

        if len(batch) < 1000:
            print(f"\nTemps réel atteint.")
            break

        time.sleep(sleep_seconds)

    df = pd.DataFrame(all_candles, columns=COLUMNS)
    df = _clean_dtypes(df)

    print(f"Terminé : {len(df):,} bougies récupérées.")
    return df


def _clean_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Convertit les colonnes dans les bons types."""
    df["Open time"] = pd.to_datetime(df["Open time"], unit="ms", utc=True)
    df["Close time"] = pd.to_datetime(df["Close time"], unit="ms", utc=True)

    numeric_cols = ["Open", "High", "Low", "Close", "Volume",
                    "Quote asset volume", "Taker buy base asset volume",
                    "Taker buy quote asset volume"]
    df[numeric_cols] = df[numeric_cols].astype(float)
    df["Number of trades"] = df["Number of trades"].astype(int)

    return df


def save_to_csv(df: pd.DataFrame, symbol: str, timeframe: str) -> Path:
    """
    Sauvegarde le DataFrame dans data/raw/{SYMBOL}_{TIMEFRAME}.csv.
    Crée le dossier si nécessaire.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    symbol_clean = symbol.replace("/", "")
    filepath = OUTPUT_DIR / f"{symbol_clean}_{timeframe}.csv"
    df.to_csv(filepath, index=False)
    print(f"Sauvegardé : {filepath}")
    return filepath


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch OHLCV data from Binance")
    parser.add_argument("--symbol",    default="BTC/USDT", help="Ex: BTC/USDT")
    parser.add_argument("--timeframe", default="15m",      help="Ex: 15m, 1h, 4h, 1d")
    parser.add_argument("--start",     default="2018-01-01", help="YYYY-MM-DD")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    df = fetch_all_ohlcv(
        symbol=args.symbol,
        timeframe=args.timeframe,
        start_date=args.start,
    )
    save_to_csv(df, symbol=args.symbol, timeframe=args.timeframe)
