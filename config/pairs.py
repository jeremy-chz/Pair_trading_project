"""
config/pairs.py
───────────────
Configuration centrale des paires et paramètres du projet.
Modifier ici plutôt que de hardcoder dans les scripts.
"""

# ── Paires actives ─────────────────────────────────────────────────────────────
PAIRS = {
    "BTC_ETH": {
        "asset_a": "BTC/USDT",
        "asset_b": "ETH/USDT",
        "timeframe": "15m",
        "description": "Paire principale crypto",
    },
    # Décommenter au fur et à mesure que tu ajoutes des paires :
    # "BTC_SOL": {
    #     "asset_a": "BTC/USDT",
    #     "asset_b": "SOL/USDT",
    #     "timeframe": "15m",
    #     "description": "Paire secondaire crypto",
    # },
}

# ── Paramètres de trading (Phase 2+) ──────────────────────────────────────────
ZSCORE_ENTRY     = 2.0   # Ouvrir une position au-delà de ce seuil
ZSCORE_EXIT      = 0.5   # Fermer la position en-dessous de ce seuil
ZSCORE_WINDOW    = 20    # Fenêtre du z-score rolling (en nombre de bougies)

# ── Paramètres du backtest (Phase 3) ──────────────────────────────────────────
TRANSACTION_COST = 0.001  # 0.1% par trade (maker Binance)
INITIAL_CAPITAL  = 10_000  # USD
