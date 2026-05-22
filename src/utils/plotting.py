"""
src/utils/plotting.py
─────────────────────
Fonctions de visualisation réutilisables pour tout le projet.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def plot_prices(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    name_a: str = "BTC",
    name_b: str = "ETH",
    figsize: tuple = (14, 5),
) -> None:
    """Prix normalisés superposés pour visualiser la corrélation brute."""
    fig, ax = plt.subplots(figsize=figsize)

    norm_a = df_a["Close"] / df_a["Close"].iloc[0]
    norm_b = df_b["Close"] / df_b["Close"].iloc[0]

    ax.plot(df_a.index, norm_a, label=name_a, linewidth=1)
    ax.plot(df_b.index, norm_b, label=name_b, linewidth=1, alpha=0.8)

    ax.set_title(f"{name_a} vs {name_b} — prix normalisés (base 1)")
    ax.set_ylabel("Prix normalisé")
    ax.legend()
    ax.grid(alpha=0.3)
    _format_xaxis(ax)
    plt.tight_layout()
    plt.show()


def plot_log_returns(
    returns_a: pd.Series,
    returns_b: pd.Series,
    name_a: str = "BTC",
    name_b: str = "ETH",
    figsize: tuple = (14, 6),
) -> None:
    """Log-returns des deux actifs côte à côte."""
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)

    for ax, ret, name, color in zip(
        axes, [returns_a, returns_b], [name_a, name_b], ["steelblue", "seagreen"]
    ):
        ax.plot(ret.index, ret, linewidth=0.6, color=color, alpha=0.8)
        ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
        ax.set_ylabel(f"Log-return {name}")
        ax.grid(alpha=0.3)

    axes[0].set_title(f"Log-returns {name_a} et {name_b}")
    _format_xaxis(axes[1])
    plt.tight_layout()
    plt.show()


def plot_rolling_correlation(
    corr: pd.Series,
    name_a: str = "BTC",
    name_b: str = "ETH",
    window: int = 30,
    figsize: tuple = (14, 4),
) -> None:
    """Corrélation mobile entre deux actifs."""
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(corr.index, corr, linewidth=1, color="steelblue")
    ax.axhline(corr.mean(), color="orange", linewidth=1,
               linestyle="--", label=f"Moyenne : {corr.mean():.2f}")
    ax.axhline(0.8, color="green", linewidth=0.8, linestyle=":", alpha=0.5)
    ax.fill_between(corr.index, corr, corr.mean(), alpha=0.1)

    ax.set_title(f"Corrélation mobile {name_a}/{name_b} (fenêtre {window} périodes)")
    ax.set_ylabel("Corrélation de Pearson")
    ax.set_ylim(-1, 1)
    ax.legend()
    ax.grid(alpha=0.3)
    _format_xaxis(ax)
    plt.tight_layout()
    plt.show()


def plot_zscore(
    zscore: pd.Series,
    entry_threshold: float = 2.0,
    exit_threshold: float = 0.5,
    figsize: tuple = (14, 4),
) -> None:
    """Z-score du spread avec seuils d'entrée/sortie."""
    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(zscore.index, zscore, linewidth=0.8, color="steelblue")
    ax.axhline(0, color="black", linewidth=0.8)

    for sign in [1, -1]:
        ax.axhline(sign * entry_threshold, color="red",
                   linewidth=1, linestyle="--", label=f"Entrée ±{entry_threshold}")
        ax.axhline(sign * exit_threshold, color="green",
                   linewidth=1, linestyle=":", label=f"Sortie ±{exit_threshold}")

    # Zones colorées
    ax.fill_between(zscore.index, entry_threshold, zscore.where(zscore > entry_threshold),
                    alpha=0.15, color="red")
    ax.fill_between(zscore.index, -entry_threshold, zscore.where(zscore < -entry_threshold),
                    alpha=0.15, color="red")

    ax.set_title("Z-score du spread")
    ax.set_ylabel("Z-score")
    # Légende sans doublons
    handles, labels = ax.get_legend_handles_labels()
    seen = {}
    for h, l in zip(handles, labels):
        if l not in seen:
            seen[l] = h
    ax.legend(seen.values(), seen.keys())
    ax.grid(alpha=0.3)
    _format_xaxis(ax)
    plt.tight_layout()
    plt.show()


def _format_xaxis(ax) -> None:
    """Formate l'axe des dates proprement."""
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")



"""def plot_spread(spread: pd.Series, figsize: tuple = (14, 5)) -> None:
    Visualise le spread brut avec sa moyenne.
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(spread.index, spread, linewidth=0.8, color='steelblue')
    ax.axhline(spread.mean(), color='red', linestyle='--', linewidth=1, 
               label=f'Moyenne : {spread.mean():.0f}')
    ax.set_title('Spread BTC − β·ETH')
    ax.legend()
    ax.grid(alpha=0.3)
    _format_xaxis(ax)
    plt.tight_layout()
    plt.show()"""


import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

def plot_spread(spread: pd.Series, figsize: tuple = (14, 5)) -> None:
    """Visualise le spread avec une gestion adaptative de l'axe X."""
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(spread.index, spread, linewidth=1, color='steelblue', label='Spread')
    
    mean_val = spread.mean()
    ax.axhline(mean_val, color='red', linestyle='--', linewidth=1, 
               label=f'Moyenne : {mean_val:.2f}')
        
    # Calcul de la durée totale des données en jours
    delta_days = (spread.index[-1] - spread.index[0]).days
    
    if delta_days <= 7:
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
    elif delta_days <= 90:
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    else:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    fig.autofmt_xdate() 
    
    ax.set_title(f'Spread BTC − β·ETH ({delta_days} jours)')
    ax.legend()
    ax.grid(visible=True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()