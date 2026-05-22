"""
src/research/cointegration.py
─────────────────────────
Analyse de la cointégration entre deux séries temporelles.
Ce module contient des fonctions pour calculer le hedge ratio (β) et tester la stationnarité du spread.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.vector_ar.vecm import coint_johansen

# ── Constantes ────────────────────────────────────────────────────────────────

COLUMNS = [
    "Open time", "Open", "High", "Low", "Close", "Volume",
    "Close time", "Quote asset volume", "Number of trades",
    "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore",
]

OUTPUT_DIR = Path("data/raw")


# ── Fonctions principales ─────────────────────────────────────────────────────

def compute_beta(price_a, price_b):
    """
    Calcule le hedge ratio β par régression OLS.
    
    β = cov(A, B) / var(B)
    
    C'est le β tel que le spread A - β·B soit le plus stationnaire possible.
    """
    return np.cov(price_a, price_b)[0, 1] / np.var(price_b, ddof=1)

# ddof=1 pour échantillon car cov avec n-1 et var avec n
# np.cov calcule la covariance échantillonnale (divisée par N-1).
# np.var calcule la variance populationnelle (divisée par N).
# Comme les données ont tendance à être plus proches de leur propre moyenne que de la vraie moyenne du marché, calculer la variance classique va sous-estimer le vrai risque.
# correction de Bessel : on doit aussi diviser par N-1 pour la variance !


# ── Spread avec β rolling ─────────────────────────────────────────────────────

def compute_rolling_spread(log_a, log_b, window):
    """
    Calcule le spread avec β rolling.
    À chaque bougie t, β est recalculé sur les `window` bougies précédentes.
    """
    spread = pd.Series(index=log_a.index, dtype=float)
    
    for i in range(window, len(log_a)):
        a_w = log_a.values[i-window:i]
        b_w = log_b.values[i-window:i]
        beta = compute_beta(a_w, b_w)
        spread.iloc[i] = log_a.iloc[i] - beta * log_b.iloc[i]
    
    return spread.dropna()

# ── Test de stationnarité ADF ─────────────────────────────────────────────────

def adf_test(spread, name='spread'):
    """
    Test ADF sur le spread.
    
    H0 : la série a une racine unitaire (non-stationnaire)
    H1 : la série est stationnaire
    
    On veut rejeter H0, donc p-value < 0.05.
    """
    result = adfuller(spread.dropna(), autolag='AIC')
    
    print(f"=== Test ADF — {name} ===")
    print(f"Statistique ADF  : {result[0]:.4f}")
    print(f"P-value          : {result[1]:.4f}")
    print(f"Valeurs critiques:")
    for level, val in result[4].items():
        print(f"   {level} : {val:.4f}")
    
    if result[1] < 0.05:
        print(f"Spread stationnaire (p={result[1]:.4f} < 0.05)")
    else:
        print(f"Spread non-stationnaire (p={result[1]:.4f} > 0.05)")
    
    return result



# ── Test de Johansen ───────────────────────────────────────────────────────────

def johansen_test(series_a, series_b, name_a='A', name_b='B'):
    """
    Test de Johansen sur deux séries de prix.
    
    Teste l'existence d'une relation de cointégration sans
    avoir besoin de calculer β à l'avance.
    
    det_order=0 : on suppose pas de tendance dans le spread
    k_ar_diff=1 : on utilise 1 lag
    """
    df = pd.DataFrame({name_a: series_a, name_b: series_b})
    
    result = coint_johansen(df, det_order=0, k_ar_diff=1)
    
    print(f"=== Test de Johansen — {name_a}/{name_b} ===\n")
    
    print("Statistiques de trace :")
    print(f"{'Hypothèse':<20} {'Statistique':>12} {'Seuil 5%':>10} {'Seuil 1%':>10} {'Résultat':>10}")
    print("-" * 65)
    
    labels = ["r=0 (aucune)", "r≤1 (au plus 1)"]
    for i in range(2):
        stat  = result.lr1[i]
        c5    = result.cvt[i, 1]
        c1    = result.cvt[i, 0]
        rejet = "rejeté" if stat > c5 else "non rejeté"
        print(f"{labels[i]:<20} {stat:>12.4f} {c5:>10.4f} {c1:>10.4f} {rejet:>10}")
    
    return result

# ── Test de Johansen sur fenêtre glissante ───────────────────────────────────

def rolling_johansen(series_a, series_b, lookback, step=96):
    timestamps = []
    betas = []
    is_cointegrated = []
    
    df = pd.DataFrame({'A': series_a.values, 'B': series_b.values}, 
                       index=series_a.index)
    
    for i in range(lookback, len(df), step):
        window = df.iloc[i-lookback:i]
        try:
            result = coint_johansen(window, det_order=0, k_ar_diff=1)
            stat = result.lr1[0]
            c5   = result.cvt[0, 1]

            evec = result.evec[:, 0]
            if evec[0] < 0:
                evec = -evec
            beta = evec[1] / evec[0]

            if abs(beta) > 1000:
                continue
            
            timestamps.append(df.index[i])
            betas.append(beta)
            is_cointegrated.append(stat > c5)
        except:
            continue

    return pd.DataFrame({
        'beta': betas,
        'cointegrated': is_cointegrated
    }, index=timestamps)


# ── Half-life du mean-reversion ────────────────────────────────────

def compute_halflife(spread):
    """
    Calcule le half-life du mean-reversion.
    
    Modèle Ornstein-Uhlenbeck :
    ΔS_t = λ·(S_{t-1} - μ) + ε_t
    
    On régresse ΔS sur S_lag pour estimer λ.
    Le half-life = -ln(2) / λ
    """
    spread = spread.dropna()
    
    delta_spread = spread.diff().dropna()
    
    spread_lag = spread.shift(1).dropna()
    
    delta_spread = delta_spread.iloc[1:]
    spread_lag = spread_lag.iloc[1:]
    
    # Régression OLS : ΔS = λ·S_lag + c
    X = np.column_stack([spread_lag.values, np.ones(len(spread_lag))])
    coeffs = np.linalg.lstsq(X, delta_spread.values, rcond=None)[0]
    
    lambda_ = coeffs[0]
    halflife = -np.log(2) / lambda_
    
    print(f"λ (vitesse de retour) : {lambda_:.6f}")
    print(f"Half-life             : {halflife:.1f} bougies")
    print(f"Half-life             : {halflife * 15 / 60:.1f} heures")
    print(f"Half-life             : {halflife * 15 / 60 / 24:.1f} jours")
    
    return halflife, lambda_


# ── Half-life empirique stricte (vagues complètes) ─────────────────────────

def compute_empirical_halflife(zscore, trigger_threshold=2.0, exit_threshold=0.5):
    """
    Calcule la Half-Life empirique en comptant uniquement les vagues complètes :
    Une vague commence quand le Z-Score franchit +- trigger_threshold,
    et ne se termine QUE lorsqu'il revient à l'intérieur de +- exit_threshold.
    """
    z_vals = zscore.values
    nb_signals = 0
    in_trade = False
    
    for val in z_vals:
        # ÉTAPE 1 : On cherche un nouveau signal (on n'est pas déjà dans une vague)
        if not in_trade:
            if abs(val) >= trigger_threshold:
                nb_signals += 1
                in_trade = True # Le robot se verrouille, la vague est en cours
                
        # ÉTAPE 2 : On attend que le Z-Score revienne vers l'équilibre pour libérer le robot
        else:
            if abs(val) <= exit_threshold:
                in_trade = False # Le spread est revenu à +- 0.5, on est prêt pour la prochaine vague
                
    if nb_signals == 0:
        print("Aucun signal complet détecté avec ces paramètres.")
        return None
        
    # Calcul de la durée totale de ton historique en jours
    total_days = (zscore.index[-1] - zscore.index[0]).total_seconds() / (24 * 3600)
    
    # Une vague complète (aller à +-2 ET retour à +-0.5)
    days_per_cycle = total_days / nb_signals
    
    # La Half-Life est le temps pour faire l'aller (de 0 à 2) OU le retour (de 2 à 0.5)
    # Dans un cycle complet "Aller + Retour", la Half-Life représente la moitié de cette durée
    halflife_days = days_per_cycle / 2
    halflife_hours = halflife_days * 24
    halflife_candles = halflife_hours * 4 # 4 bougies de 15 minutes par heure
    
    print("="*45)
    print(f"--- ANALYSE STRICTE DES VAGUES (ALLER-RETOUR) ---")
    print(f"Période analysée       : {total_days:.1f} jours")
    print(f"Vagues validées (Aller-Retour) : {nb_signals} fois")
    print(f"Durée moyenne d'un cycle complet: {days_per_cycle:.1f} jours")
    print("-"*45)
    print(f"VRAIE HALF-LIFE PHYSIQUE : {halflife_candles:.1f} bougies")
    print(f"                         : {halflife_hours:.1f} heures")
    print(f"                         : {halflife_days:.1f} jours")
    print("="*45)
    
    return halflife_candles