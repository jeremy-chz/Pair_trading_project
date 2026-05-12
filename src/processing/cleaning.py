"""
src/processing/cleaning.py
──────────────────────────
Nettoyage et alignement temporel des séries OHLCV.

Fonctions principales :
    load_ohlcv()     → charge un CSV brut depuis data/raw/
    align_pairs()    → aligne deux séries sur leurs timestamps communs
    detect_gaps()    → identifie les trous dans une série temporelle
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


# ── Chargement ────────────────────────────────────────────────────────────────

def load_ohlcv(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Charge un fichier CSV brut depuis data/raw/.

    Args:
        symbol    : ex "BTCUSDT" ou "BTC/USDT" (le slash est retiré)
        timeframe : ex "15m"

    Returns:
        DataFrame avec 'Open time' comme index DatetimeTZDtype UTC.
    """
    symbol_clean = symbol.replace("/", "")
    filepath = RAW_DIR / f"{symbol_clean}_{timeframe}.csv"

    if not filepath.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {filepath}\n"
            f"Lance d'abord : python src/ingestion/get_data.py --symbol {symbol} --timeframe {timeframe}"
        )

    df = pd.read_csv(filepath)

    for col in ["Open time", "Close time"]:
        df[col] = pd.to_datetime(df[col], utc=True)

    df = df.set_index("Open time").sort_index()

    print(f"Chargé : {symbol_clean}_{timeframe} — {len(df):,} bougies "
          f"({df.index[0].date()} → {df.index[-1].date()})")
    return df


# ── Alignement ────────────────────────────────────────────────────────────────

def align_pairs(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    name_a: str = "A",
    name_b: str = "B",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aligne deux séries OHLCV sur leurs timestamps communs (inner join).
    Les bougies sans correspondance dans l'autre série sont supprimées.

    Pourquoi c'est important :
        Un spread calculé sur des timestamps non-alignés compare des prix
        à des moments différents → signal bruité et potentiellement faux.

    Returns:
        (df_a_aligned, df_b_aligned) — même index, même longueur.
    """
    common_index = df_a.index.intersection(df_b.index)

    lost_a = len(df_a) - len(common_index)
    lost_b = len(df_b) - len(common_index)

    print(f"Alignement {name_a} / {name_b}")
    print(f"  {name_a} : {len(df_a):,} bougies  →  perdues : {lost_a}")
    print(f"  {name_b} : {len(df_b):,} bougies  →  perdues : {lost_b}")
    print(f"  Timestamps communs : {len(common_index):,}")

    if lost_a > 100 or lost_b > 100:
        print(f"  ⚠ Beaucoup de bougies perdues — vérifie les gaps avec detect_gaps()")

    return df_a.loc[common_index], df_b.loc[common_index]


# ── Détection des gaps ────────────────────────────────────────────────────────

def detect_gaps(df: pd.DataFrame, timeframe_minutes: int = 15) -> pd.Series:
    """
    Détecte les trous dans une série temporelle.

    Un gap est un intervalle entre deux bougies supérieur à 1.5× le timeframe attendu.
    (Le facteur 1.5 évite les faux positifs liés aux arrondis de timestamps.)

    Args:
        df                 : DataFrame avec index DatetimeTZDtype
        timeframe_minutes  : Durée attendue entre deux bougies en minutes

    Returns:
        Series des gaps détectés (index = timestamp du gap, valeur = durée)
    """
    expected = pd.Timedelta(minutes=timeframe_minutes)
    deltas = df.index.to_series().diff()
    gaps = deltas[deltas > expected * 1.5]

    if gaps.empty:
        print("Aucun gap détecté.")
    else:
        print(f"{len(gaps)} gap(s) détecté(s) :")
        for ts, delta in gaps.items():
            print(f"  {ts.date()}  →  durée : {delta}")

    return gaps


# ── Sauvegarde ────────────────────────────────────────────────────────────────

def save_processed(df: pd.DataFrame, filename: str) -> Path:
    """Sauvegarde dans data/processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    filepath = PROCESSED_DIR / filename
    df.to_csv(filepath)
    print(f"Sauvegardé : {filepath}")
    return filepath
