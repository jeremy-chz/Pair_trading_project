# Data

Les fichiers CSV ne sont pas versionnés (trop volumineux pour Git).

## Régénérer les données

```bash
# Depuis la racine du projet
python src/ingestion/get_data.py --symbol BTC/USDT --timeframe 15m --start 2018-01-01
python src/ingestion/get_data.py --symbol ETH/USDT --timeframe 15m --start 2018-01-01
```

## Structure attendue après génération

```
data/
├── raw/
│   ├── BTCUSDT_15m.csv
│   ├── ETHUSDT_15m.csv
│   └── ...
└── processed/
    ├── BTCUSDT_ETHUSDT_aligned.csv    # après src/processing/align.py
    └── ...
```

## Convention de nommage

`{SYMBOL}_{TIMEFRAME}.csv`  →  ex : `BTCUSDT_15m.csv`, `SOLUSDT_1h.csv`
