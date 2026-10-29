"""Cas swing calculés par src/tradeperso/strategies.py, pour vérifier que l'app calcule pareil.
Usage, à la racine du dépôt : python app/scripts/parite_swing.py"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tradeperso.strategies import STRATEGIES

rng = np.random.default_rng(11)
cas = []
for graine, (derive, vol) in enumerate([(0.0008, 0.01), (-0.0008, 0.01), (0.0, 0.012)]):
    n = 500
    c = 20000 * np.exp(np.cumsum(rng.normal(derive, vol, n)))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, vol / 4, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, vol / 2, n)))
    lo = np.minimum(o, c) * (1 - np.abs(rng.normal(0, vol / 2, n)))
    df = pd.DataFrame({"Open": o, "High": h, "Low": lo, "Close": c}, index=pd.bdate_range(end="2026-10-28", periods=n))
    regles = {}
    for nom in ["tendance_mm", "rsi2_repli", "cassure_20j", "repli_tendance", "tendance_mm_vente", "cassure_20j_vente"]:
        out = STRATEGIES[nom].fonction(df)
        e = out["entry"].fillna(False).astype(bool)
        regles[nom] = {"entree": e.tolist(),
                       "stop": [None if pd.isna(x) else float(x) for x in out["stop"]],
                       "objectif": [None if pd.isna(x) else float(x) for x in out["target"]]}
    cas.append({"bougies": [{"t": int((t + pd.Timedelta(hours=12)).timestamp() * 1000), "o": r.Open, "h": r.High, "l": r.Low,
                             "c": r.Close} for t, r in df.iterrows()], "regles": regles})
Path(__file__).resolve().parent.parent.joinpath("src/domain/__fixtures__/parite_swing.json").write_text(
    json.dumps(cas), encoding="utf-8")
print({k: sum(v["entree"]) for x in cas for k, v in x["regles"].items()})
