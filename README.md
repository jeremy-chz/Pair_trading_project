# Pair Trading — BTC/ETH → Quant ML

Projet personnel de recherche quantitative : construction d'une stratégie de pair trading
sur crypto (BTC/ETH), avec extension progressive vers les actions et le machine learning.

## Objectif

Partir des fondamentaux statistiques (cointégration, mean-reversion) pour arriver
à des modèles ML quantitatifs sérieux (LSTM, RL, Gaussian Processes).
Chaque phase est documentée pour que mon raisonnement soit compréhensible, pas juste le code.

## Roadmap

| Phase | Contenu | Status |
|-------|---------|--------|
| 1 | Data engineering — ingestion, alignement, log-returns | En cours |
| 2 | Cointégration — ADF, Johansen, spread, z-score | x |
| 3 | Backtesting — walk-forward, Sharpe, drawdown | x |
| 4 | Séries temporelles — ARIMA, GARCH, Kalman, Ornstein-Uhlenbeck | x |
| 5 | ML quantitatif — LSTM, RL, Gaussian Processes | x |

## Structure

```
pair_trading/
├── data/
│   ├── raw/          # CSV Binance bruts — non versionnés (voir ci-dessous)
│   └── processed/    # Données alignées, nettoyées, prêtes à l'emploi
├── src/
│   ├── ingestion/    # Fetch Binance via ccxt
│   ├── processing/   # Alignement temporel, nettoyage
│   ├── features/     # Log-returns, z-score, indicateurs
│   ├── research/     # Cointégration, backtesting, modèles
│   ├── execution/    # (Phase 3+) Simulation d'ordres
│   └── utils/        # Fonctions partagées (plots, helpers)
├── notebooks/        # Exploration et documentation par phase
├── tests/            # Tests unitaires
└── config/           # Paramètres (paires, timeframes, seuils)
```

## Données

Les fichiers CSV ne sont pas versionnés. Pour les régénérer :

```bash
python src/ingestion/get_data.py --symbol BTC/USDT --timeframe 15m --start 2018-01-01
python src/ingestion/get_data.py --symbol ETH/USDT --timeframe 15m --start 2018-01-01
```

## Installation

```bash
git clone https://github.com/TON_USERNAME/pair_trading.git
cd pair_trading
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## Lancer les notebooks

```bash
jupyter notebook notebooks/
```
