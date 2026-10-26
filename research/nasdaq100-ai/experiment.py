"""Expérience NASDAQ100: signal à la clôture J, aller-retour théorique ouverture/clôture J+1.

Étude uniquement: les points d'indice ne constituent pas un instrument négociable.
Aucune connexion broker, aucun ordre réel, aucune promesse d'alpha.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = ["return_1d", "return_5d", "ma20_gap", "range_pct", "gap_pct", "volatility_20d"]
COST_BPS = 15.0  # hypothèse de simulation, NON les coûts réels eToro/IG
THRESHOLD = 0.55


def load_ohlc(path: str | Path) -> pd.DataFrame:
    """CSV explicite: Date,Open,High,Low,Close; tri et validations fail-closed."""
    frame = pd.read_csv(path)
    required = {"Date", "Open", "High", "Low", "Close"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Colonnes nécessaires: {sorted(required)}")
    frame = frame[list(required)].copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise")
    if frame["Date"].isna().any() or frame["Date"].duplicated().any():
        raise ValueError("Dates manquantes ou doublonnées")
    frame = frame.sort_values("Date").set_index("Date")
    for col in ("Open", "High", "Low", "Close"):
        frame[col] = pd.to_numeric(frame[col], errors="raise")
    if frame.isna().any().any() or (frame <= 0).any().any():
        raise ValueError("Prix absents, nuls ou négatifs")
    if ((frame["High"] < frame[["Open", "Close", "Low"]].max(axis=1)) |
        (frame["Low"] > frame[["Open", "Close", "High"]].min(axis=1))).any():
        raise ValueError("Bougie OHLC incohérente")
    return frame


def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    """Features disponibles à J clôture; label J+1 sans fuite future."""
    c, o, h, l = (raw[k].astype(float) for k in ("Close", "Open", "High", "Low"))
    ret1 = c.pct_change()
    target = c.shift(-1) / o.shift(-1) - 1.0
    x = pd.DataFrame(index=raw.index)
    x["return_1d"] = ret1
    x["return_5d"] = c.pct_change(5)
    x["ma20_gap"] = c / c.rolling(20).mean() - 1.0
    x["range_pct"] = (h - l) / o
    x["gap_pct"] = o / c.shift(1) - 1.0
    x["volatility_20d"] = ret1.rolling(20).std()
    x["next_intraday_return"] = target
    x = x.replace([np.inf, -np.inf], np.nan).dropna()
    x["label"] = (x["next_intraday_return"] > 0.0).astype(int)
    return x


def chronological_blocks(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """70/15/15 avec une journée purgée entre les blocs (horizon label 1)."""
    n = len(df)
    if n < 300:
        raise ValueError("Au moins 300 journées exploitables requises")
    cut1, cut2 = int(n * 0.70), int(n * 0.85)
    train = df.iloc[: cut1 - 1]
    validation = df.iloc[cut1 : cut2 - 1]
    test = df.iloc[cut2:]
    if not (len(train) and len(validation) and len(test)):
        raise ValueError("Partage temporel impossible")
    return train, validation, test


def model_candidates():
    """Baseline + deux modèles CPU; GPU et LLM inutiles pour cette expérience."""
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return {
        "prior_only": DummyClassifier(strategy="prior"),
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=42)),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_iter=90, max_leaf_nodes=9, learning_rate=0.05, random_state=42
        ),
    }


def score(model, sample: pd.DataFrame) -> dict:
    proba = model.predict_proba(sample[FEATURES])[:, 1]
    signal = proba >= THRESHOLD
    # Hypothèse: décision à la clôture J, achat ouverture J+1, sortie clôture J+1.
    # Un aller-retour J+1 par signal; frais hypothétiques appliqués chaque fois.
    daily = np.where(signal, sample["next_intraday_return"].to_numpy() - COST_BPS / 10000, 0.0)
    equity = np.cumprod(1.0 + daily)
    peak = np.maximum.accumulate(np.concatenate([[1.0], equity]))[1:]
    baseline = sample["next_intraday_return"].to_numpy() - COST_BPS / 10000
    from sklearn.metrics import brier_score_loss, roc_auc_score

    labels = sample["label"].to_numpy()
    auc = float(roc_auc_score(labels, proba)) if len(np.unique(labels)) > 1 else None
    return {
        "days": len(sample),
        "signals": int(signal.sum()),
        "roc_auc": round(auc, 4) if auc is not None else None,
        "brier": round(float(brier_score_loss(labels, proba)), 5),
        "net_return_pct": round(float((equity[-1] - 1) * 100), 3),
        "max_drawdown_pct": round(float(np.min(equity / peak - 1) * 100), 3),
        "always_long_net_return_pct": round(float((np.prod(1 + baseline) - 1) * 100), 3),
    }


def evaluate(path: str | Path) -> dict:
    raw = load_ohlc(path)
    dataset = prepare(raw)
    train, val, test = chronological_blocks(dataset)
    if train["label"].nunique() < 2:
        raise ValueError("Entraînement impossible: une seule classe")
    trained = {}
    validation = {}
    for name, model in model_candidates().items():
        model.fit(train[FEATURES], train["label"])
        trained[name] = model
        validation[name] = score(model, val)
    # Sélection sur validation exclusivement, test consulté une seule fois après gel.
    champion = max(validation, key=lambda name: (validation[name]["net_return_pct"], -validation[name]["brier"]))
    csv_hash = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return {
        "index": "Nasdaq 100", "symbol": "^NDX",
        "instrument": "indice non négociable directement",
        "data_sha256": csv_hash, "features": FEATURES, "label": "retour open->close J+1 positif",
        "cost_bps_roundtrip_hypothesis": COST_BPS, "buy_threshold": THRESHOLD,
        "splits": {
            k: {"count": len(b), "first": str(b.index[0].date()), "last": str(b.index[-1].date())}
            for k, b in (("train", train), ("validation", val), ("test", test))
        },
        "validation": validation, "champion": champion,
        "test_once_out_of_sample": score(trained[champion], test),
        "status": "RESEARCH_ONLY_NOT_TRADING_AUTHORIZED",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Lab ML NASDAQ100, long/flat, sans exécution réelle")
    p.add_argument("--csv", required=True, help="CSV OHLC fiable et daté")
    p.add_argument("--output", default=None, help="Enregistrer le rapport JSON")
    args = p.parse_args()
    report = evaluate(args.csv)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
