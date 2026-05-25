"""
src/research/backtesting.py
───────────────────────────
Fonctions de backtesting pour la stratégie de pair trading.

Pipeline :
    generate_signals()      → signaux d'entrée/sortie basés sur le z-score
    simulate_pnl_real()     → P&L dollar-neutral avec frais de transaction
    compute_metrics()       → Sharpe, drawdown, win rate, return total
    walk_forward()          → test sur fenêtres glissantes (robustesse)
    plot_pnl()              → visualisation du P&L cumulé
    plot_walk_forward()     → visualisation du Sharpe par fenêtre
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ── Génération des signaux ────────────────────────────────────────────────────

def generate_signals(zscore: pd.Series, entry: float = 2.0, exit: float = 0.5) -> pd.Series:
    """
    Génère les signaux de trading à partir du z-score.

    Logique :
        z > +entry  → short spread (vend BTC, achète ETH)
        z < -entry  → long spread  (achète BTC, vend ETH)
        |z| < exit  → ferme la position

    On ne rentre pas dans une nouvelle position tant que la précédente
    n'est pas fermée — évite le surtrading.

    Args:
        zscore : Series du z-score du spread
        entry  : Seuil d'entrée en position (défaut : 2.0)
        exit   : Seuil de sortie de position (défaut : 0.5)

    Returns:
        Series avec :
         1 = long spread
        -1 = short spread
         0 = pas de position
    """
    signal = pd.Series(0, index=zscore.index, dtype=int)
    position = 0

    for i in range(len(zscore)):
        z = zscore.iloc[i]

        if np.isnan(z):
            continue

        if position == 0:
            if z > entry:
                position = -1
            elif z < -entry:
                position = 1
        else:
            if abs(z) < exit:
                position = 0

        signal.iloc[i] = position

    return signal


# ── Simulation du P&L ─────────────────────────────────────────────────────────

def simulate_pnl_real(
    df_btc: pd.DataFrame,
    df_eth: pd.DataFrame,
    signal: pd.Series,
    beta: float,
    capital: float = 10_000,
    transaction_cost: float = 0.001,
) -> pd.Series:
    """
    Simule le P&L dollar-neutral de la stratégie.

    Dollar-neutral :
        Long spread  = achète capital/2 de BTC, vend β × capital/2 de ETH
        Short spread = vend capital/2 de BTC, achète β × capital/2 de ETH

    Le shift(1) sur le signal évite le look-ahead bias :
        le signal de la bougie t ne peut pas utiliser le prix de t.

    Args:
        df_btc           : DataFrame BTC avec colonne 'Close'
        df_eth           : DataFrame ETH avec colonne 'Close'
        signal           : Series des signaux (1, -1, 0)
        beta             : Hedge ratio β
        capital          : Capital total en dollars (défaut : 10 000$)
        transaction_cost : Frais par trade en % (défaut : 0.1%)

    Returns:
        Series du P&L net par bougie en dollars.
    """
    ret_btc = df_btc['Close'].pct_change()
    ret_eth = df_eth['Close'].pct_change()

    # P&L brut : on alloue capital/2 sur chaque leg
    # Le signal shifté d'1 bougie évite le look-ahead
    pnl = signal.shift(1) * (ret_btc - beta * ret_eth) * (capital / 2)

    # Frais à chaque changement de position
    position_changes = signal.diff().abs() > 0
    costs = position_changes * capital * transaction_cost

    return pnl - costs


# ── Métriques de performance ──────────────────────────────────────────────────

def compute_metrics(
    pnl: pd.Series,
    capital: float = 10_000,
    timeframe_minutes: int = 15,
) -> dict:
    """
    Calcule les métriques de performance de la stratégie.

    Métriques :
        Sharpe ratio  : return moyen / volatilité, annualisé
        Return total  : P&L cumulé en dollars
        Max drawdown  : perte maximale depuis un pic
        Win rate      : % de bougies avec P&L positif

    Args:
        pnl               : Series du P&L par bougie
        capital           : Capital initial en dollars
        timeframe_minutes : Durée d'une bougie en minutes (défaut : 15)

    Returns:
        Dictionnaire des métriques.
    """
    # Nombre de bougies par an pour l'annualisation
    bougies_par_an = 365 * 24 * (60 / timeframe_minutes)

    returns = pnl / capital
    sharpe = returns.mean() / returns.std() * np.sqrt(bougies_par_an) if returns.std() > 0 else 0

    cumret = pnl.cumsum()
    drawdown = cumret - cumret.cummax()
    max_dd = drawdown.min()

    metrics = {
        'sharpe':       round(sharpe, 3),
        'return_total': round(pnl.sum(), 0),
        'max_drawdown': round(max_dd, 0),
        'win_rate':     round((pnl > 0).mean() * 100, 1),
        'nb_trades':    int((pnl != 0).sum()),
    }

    print(f"Sharpe ratio      : {metrics['sharpe']}")
    print(f"Return total      : {metrics['return_total']}$")
    print(f"Max drawdown      : {metrics['max_drawdown']}$")
    print(f"Win rate          : {metrics['win_rate']}%")

    return metrics


def compute_metrics_clean(
    pnl: pd.Series,
    signal: pd.Series,
    capital: float = 10_000,
    timeframe_minutes: int = 15,
) -> dict:
    """
    Version propre de compute_metrics avec le signal en paramètre.

    Args:
        pnl               : Series du P&L par bougie
        signal            : Series des signaux (1, -1, 0)
        capital           : Capital initial
        timeframe_minutes : Durée d'une bougie en minutes

    Returns:
        Dictionnaire des métriques.
    """
    bougies_par_an = 365 * 24 * (60 / timeframe_minutes)

    returns = pnl / capital
    sharpe = returns.mean() / returns.std() * np.sqrt(bougies_par_an) if returns.std() > 0 else 0

    cumret = pnl.cumsum()
    drawdown = cumret - cumret.cummax()
    max_dd = drawdown.min()

    nb_trades = int((signal.diff().abs() > 0).sum())

    metrics = {
        'sharpe':       round(sharpe, 3),
        'return_total': round(pnl.sum(), 0),
        'max_drawdown': round(max_dd, 0),
        'win_rate':     round((pnl > 0).mean() * 100, 1),
        'nb_trades':    nb_trades,
    }

    print(f"Sharpe ratio      : {metrics['sharpe']}")
    print(f"Return total      : {metrics['return_total']}$")
    print(f"Max drawdown      : {metrics['max_drawdown']}$")
    print(f"Win rate          : {metrics['win_rate']}%")
    print(f"Nombre de trades  : {metrics['nb_trades']}")

    return metrics


# ── Walk-forward validation ───────────────────────────────────────────────────

def walk_forward(
    pnl: pd.Series,
    signal: pd.Series,
    window_days: int = 180,
    step_days: int = 90,
    capital: float = 10_000,
    timeframe_minutes: int = 15,
) -> pd.DataFrame:
    """
    Walk-forward validation : teste la stratégie sur des fenêtres glissantes.

    Pourquoi c'est important :
        Un backtest sur une seule période peut être chanceux.
        Le walk-forward teste si la stratégie est robuste sur TOUTES les périodes.
        Si le Sharpe est positif sur 80%+ des fenêtres → stratégie robuste.
        Si positif sur 30% seulement → stratégie non robuste.

    Args:
        pnl             : Series du P&L par bougie
        signal          : Series des signaux
        window_days     : Taille de chaque fenêtre de test en jours
        step_days       : Pas entre deux fenêtres en jours
        capital         : Capital initial
        timeframe_minutes : Durée d'une bougie

    Returns:
        DataFrame avec sharpe et return par fenêtre.
    """
    bougies_par_an = 365 * 24 * (60 / timeframe_minutes)
    window = window_days * 24 * (60 // timeframe_minutes)
    step   = step_days  * 24 * (60 // timeframe_minutes)

    results = []

    for i in range(window, len(pnl), step):
        pnl_w    = pnl.iloc[i-window:i]
        signal_w = signal.iloc[i-window:i]

        returns = pnl_w / capital
        sharpe  = returns.mean() / returns.std() * np.sqrt(bougies_par_an) if returns.std() > 0 else 0
        nb_trades = int((signal_w.diff().abs() > 0).sum())

        results.append({
            'start':     pnl.index[i-window],
            'end':       pnl.index[i-1],
            'sharpe':    round(sharpe, 3),
            'return':    round(pnl_w.sum(), 0),
            'nb_trades': nb_trades,
        })

    df = pd.DataFrame(results).set_index('start')

    pct_positive = (df['sharpe'] > 0).mean() * 100
    print(f"Sharpe positif : {pct_positive:.0f}% des fenêtres")
    print(f"Sharpe moyen   : {df['sharpe'].mean():.3f}")
    print(f"Sharpe min     : {df['sharpe'].min():.3f}")
    print(f"Sharpe max     : {df['sharpe'].max():.3f}")

    return df


# ── Visualisation ─────────────────────────────────────────────────────────────

def plot_pnl(pnl: pd.Series, title: str = 'P&L cumulé', figsize: tuple = (14, 5)) -> None:
    """Visualise le P&L cumulé en dollars avec le drawdown."""
    cumret  = pnl.cumsum()
    drawdown = cumret - cumret.cummax()

    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True,
                              gridspec_kw={'height_ratios': [3, 1]})

    # P&L cumulé
    axes[0].plot(cumret.index, cumret, linewidth=1, color='steelblue')
    axes[0].axhline(0, color='red', linewidth=0.8, linestyle='--')
    axes[0].set_title(title)
    axes[0].set_ylabel('P&L cumulé ($)')
    axes[0].grid(alpha=0.3)

    # Drawdown
    axes[1].fill_between(drawdown.index, drawdown, 0, alpha=0.4, color='red')
    axes[1].set_ylabel('Drawdown ($)')
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.show()


def plot_walk_forward(df_wf: pd.DataFrame, figsize: tuple = (14, 4)) -> None:
    """Visualise le Sharpe ratio par fenêtre walk-forward."""
    fig, ax = plt.subplots(figsize=figsize)

    colors = ['steelblue' if s > 0 else 'tomato' for s in df_wf['sharpe']]
    ax.bar(df_wf.index, df_wf['sharpe'], color=colors, width=60, alpha=0.7)
    ax.axhline(0, color='black', linewidth=0.8)
    ax.axhline(1, color='green', linewidth=0.8, linestyle='--', alpha=0.5, label='Sharpe = 1')

    ax.set_title('Sharpe ratio par fenêtre de 6 mois (walk-forward)')
    ax.set_ylabel('Sharpe ratio')
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()