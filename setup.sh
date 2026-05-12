#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# setup.sh — Initialisation complète du repo pair_trading
# Usage : bash setup.sh
# ══════════════════════════════════════════════════════════════════════════════

set -e  # Arrêter si une commande échoue

echo "═══════════════════════════════════════"
echo "  Setup pair_trading"
echo "═══════════════════════════════════════"

# ── 1. Git ────────────────────────────────────────────────────────────────────
echo ""
echo "→ Initialisation Git..."
git init
git branch -M main

# ── 2. Environnement virtuel ──────────────────────────────────────────────────
echo ""
echo "→ Création de l'environnement virtuel..."
python3 -m venv venv

echo ""
echo "→ Activation et installation des dépendances..."
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows — décommenter cette ligne à la place

pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo ""
echo "→ Enregistrement du kernel Jupyter..."
python -m ipykernel install --user --name=pair_trading --display-name "Python (pair_trading)"

# ── 3. Premier commit ─────────────────────────────────────────────────────────
echo ""
echo "→ Premier commit..."
git add .
git commit -m "init: structure du projet pair trading

- src/ : ingestion, processing, features, utils
- notebooks/ : 01_data_exploration.ipynb
- tests/ : test_ingestion, test_cleaning
- config/ : pairs.py
- data/ : non versionné (.gitignore), README pour régénérer"

echo ""
echo "═══════════════════════════════════════"
echo "  Setup terminé !"
echo ""
echo "  Prochaines étapes :"
echo "  1. Crée ton repo sur github.com"
echo "  2. git remote add origin https://github.com/TON_USERNAME/pair_trading.git"
echo "  3. git push -u origin main"
echo ""
echo "  Pour récupérer les données :"
echo "  python src/ingestion/get_data.py --symbol BTC/USDT --timeframe 15m --start 2018-01-01"
echo "  python src/ingestion/get_data.py --symbol ETH/USDT --timeframe 15m --start 2018-01-01"
echo ""
echo "  Pour lancer les tests :"
echo "  pytest tests/"
echo "═══════════════════════════════════════"
