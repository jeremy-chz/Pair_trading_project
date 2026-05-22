"""
src/features/features.py
────────────────────────
Calcul des features financières de base.

Concepts clés :
    log_returns      → r_t = ln(P_t / P_{t-1})
    rolling_zscore   → (x - mean) / std sur fenêtre glissante
    rolling_corr     → corrélation mobile entre deux séries

Ces features sont le point d'entrée de toute analyse quantitative.
Les prix bruts ne sont presque jamais utilisés directement.
"""

import numpy as np
import pandas as pd


# ── Log-returns ───────────────────────────────────────────────────────────────

def log_returns(prices: pd.Series) -> pd.Series:
    """
    Calcule les log-returns d'une série de prix.

    Formule : r_t = ln(P_t / P_{t-1})

    Pourquoi log et pas (P_t - P_{t-1}) / P_{t-1} ?
        - Additivité temporelle : r(t1→t3) = r(t1→t2) + r(t2→t3)
        - Symétrie : +10% et -10% sont exactement opposés
        - Stationnarité : les log-returns oscillent autour de 0,
          contrairement aux prix qui ont une tendance

    Le premier élément est NaN par construction (pas de P_{t-1}).

    Args:
        prices : Series de prix de clôture (ou open, high, low)

    Returns:
        Series de log-returns, même index que prices.
    """
    return np.log(prices / prices.shift(1))


# ── Z-score rolling ───────────────────────────────────────────────────────────

def rolling_zscore(series: pd.Series, window: int = 20) -> pd.Series:
    """
    Z-score sur fenêtre glissante.

    Formule : z_t = (x_t - mean_{t-window:t}) / std_{t-window:t}

    Interprétation : "combien d'écarts-types au-dessus de la moyenne récente ?"

    Usage en pair trading :
        - Appliqué au spread → signal de trading
        - z > +2 : spread trop élevé → vendre l'écart (short A, long B)
        - z < -2 : spread trop faible → acheter l'écart (long A, short B)
        - z ≈ 0  : fermer la position

    Pourquoi rolling et pas global ?
        Le z-score global suppose que la moyenne et la variance sont constantes
        dans le temps. En finance, elles ne le sont pas (non-stationnarité).
        La fenêtre glissante s'adapte aux régimes de marché.

    Args:
        series : Series de valeurs (spread, prix, returns...)
        window : Taille de la fenêtre en nombre de périodes

    Returns:
        Series de z-scores, NaN pour les window-1 premières valeurs.
    """
    rolling_mean = series.rolling(window).mean()
    rolling_std  = series.rolling(window).std()
    return (series - rolling_mean) / rolling_std


# ── Corrélation mobile ────────────────────────────────────────────────────────

def rolling_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    window: int = 30,
) -> pd.Series:
    """
    Corrélation de Pearson sur fenêtre glissante.

    Usage :
        Vérifier que la corrélation entre BTC et ETH reste stable dans le temps.
        Une corrélation qui s'effondre = la paire perd sa cohérence.

    Args:
        series_a, series_b : Deux séries de même index (ex : log-returns)
        window             : Fenêtre en nombre de périodes

    Returns:
        Series de corrélations ∈ [-1, 1].
    """
    return series_a.rolling(window).corr(series_b)


# ── Volatilité réalisée ───────────────────────────────────────────────────────

def realized_volatility(log_ret: pd.Series, window: int = 20) -> pd.Series:
    """
    Volatilité réalisée = écart-type des log-returns sur fenêtre glissante.

    Annualisée en multipliant par sqrt(N_périodes_par_an).
    Pour du 15m : N = 4 * 24 * 365 = 35040

    Note : on ne l'annualise pas ici pour garder la flexibilité.

    Args:
        log_ret : Series de log-returns
        window  : Fenêtre en nombre de périodes

    Returns:
        Series de volatilités réalisées.
    """
    return log_ret.rolling(window).std()