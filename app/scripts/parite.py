"""Fixe des cas calculés par le code Python (plan.py, indicators.py) pour vérifier que l'app calcule pareil.
Usage, à la racine du dépôt : python app/scripts/parite.py"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tradeperso import plan
from tradeperso.indicators import atr, rsi, sma

rng = np.random.default_rng(7)


def marche(n: int, depart: float, vol: float) -> pd.DataFrame:
    c = depart + np.cumsum(rng.normal(0, vol, n))
    o = np.r_[depart, c[:-1]] + rng.normal(0, vol / 4, n)
    h = np.maximum(o, c) + np.abs(rng.normal(0, vol / 2, n))
    lo = np.minimum(o, c) - np.abs(rng.normal(0, vol / 2, n))
    return pd.DataFrame({"Open": o, "High": h, "Low": lo, "Close": c})


def bougies(df: pd.DataFrame) -> list[dict]:
    return [{"t": int(t.timestamp() * 1000), "o": r.Open, "h": r.High, "l": r.Low, "c": r.Close} for t, r in df.iterrows()]


cas = {"indices": {}}
for s, info in plan.INDICES.items():
    depart = {"^GDAXI": 24000, "^NDX": 30000, "^GSPC": 7000}[s]
    d = marche(300, depart, depart * 0.01)
    d.index = pd.bdate_range(end="2026-10-27", periods=300)
    d.index = d.index + pd.Timedelta(hours=12)
    # 30 min sur 5 jours ouvrés autour du passage à l'heure d'hiver (25 octobre)
    jours = pd.bdate_range("2026-10-22", "2026-10-28")
    idx = pd.DatetimeIndex([j + pd.Timedelta(minutes=30 * k) for j in jours for k in range(16, 44)]).tz_localize("Europe/Paris")
    h = marche(len(idx), depart, depart * 0.002)
    h.index = idx
    regle = {"^GDAXI": "cassure-0.25-tendance"}.get(s, "cassure-0.25-aucun")
    pl = plan.preparer(pd.Timestamp("2026-10-28 08:45", tz="Europe/Paris"), {"indices": {s: {"choisie": regle}}},
                       {s: d.assign()}, {s: h}, {})
    c = d["Close"]
    rejeux = []
    us = info.get("us", False)
    for jour, g in plan.seances(h, info["heures"], info.get("debut_min", 0), us).items():
        for k in (0.1, 0.3):
            liste = plan.ordres(plan.PAR_CLE[f"cassure-{0.25}-aucun"], float(g["High"].iloc[:3].max()) + k * 10,
                                float(g["Low"].iloc[:3].min()) - k * 10, depart * 0.004, 1)
            t = plan.rejouer(g, liste, info["fin_entree"], info["spread"], True, us=us)
            rejeux.append({"jour": str(jour), "ordres": [o.__dict__ for o in liste],
                           "trade": None if t is None else {**t.__dict__}})
    from tradeperso.horaire import pivots_semaine
    cas["indices"][s] = {
        "quotidien": bougies(d), "intraday": bougies(h), "regle": regle,
        "plan": pl["indices"].get(s),
        "sma20": sma(c, 20).iloc[-5:].tolist(), "atr": atr(d).iloc[-5:].tolist(), "rsi": rsi(c, 14).iloc[-5:].tolist(),
        "rejeux": rejeux, "pivots": pivots_semaine(d, pd.Timestamp("2026-10-28").date()),
    }
Path(__file__).resolve().parent.parent.joinpath("src/domain/__fixtures__/parite.json").write_text(
    json.dumps(cas, default=float), encoding="utf-8")
print("ok")
