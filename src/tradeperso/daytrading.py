"""Day trading sur indices en options barrières IG : cassure du plus haut ou du plus bas de la veille.

Plan calculé le soir pour la séance suivante :
- achat si le cours dépasse le plus haut de la veille (+ marge), vente s'il passe sous le plus bas (- marge) ;
- un seul côté par jour (le premier niveau touché) ;
- knock-out (stop) à `k_stop` ATR du point d'entrée, objectif à `ratio` fois ce risque ;
- clôture obligatoire en fin de séance si ni le stop ni l'objectif n'est touché.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .indicators import atr, sma


@dataclass
class Niveaux:
    achat: float
    achat_ko: float
    achat_objectif: float
    vente: float
    vente_ko: float
    vente_objectif: float


def niveaux(h: float, l: float, a: float, k_stop: float = 0.5, marge: float = 0.1, ratio: float = 3.0) -> Niveaux:
    achat, vente = h + marge * a, l - marge * a
    risque = k_stop * a
    return Niveaux(achat, achat - risque, achat + ratio * risque, vente, vente + risque, vente - ratio * risque)


def filtre_jour(df: pd.DataFrame, nom: str) -> pd.Series:
    """Jours (à la clôture) où le plan du lendemain est autorisé."""
    rng = df["High"] - df["Low"]
    if nom == "tous":
        return pd.Series(True, index=df.index)
    if nom == "nr4":  # séance la plus étroite des 4 dernières : compression avant expansion
        return rng <= rng.rolling(4).min()
    if nom == "inside":  # séance comprise dans la précédente
        return (df["High"] <= df["High"].shift(1)) & (df["Low"] >= df["Low"].shift(1))
    raise ValueError(nom)


def sens_autorise(df: pd.DataFrame, nom: str) -> tuple[pd.Series, pd.Series]:
    """(achat autorisé, vente autorisée) selon le filtre de tendance."""
    vrai = pd.Series(True, index=df.index)
    if nom == "deux_sens":
        return vrai, vrai
    if nom == "tendance":  # dans le sens de la moyenne 20 jours
        m = sma(df["Close"], 20)
        return df["Close"] > m, df["Close"] < m
    raise ValueError(nom)


def backtest(df: pd.DataFrame, filtre: str = "tous", tendance: str = "deux_sens", k_stop: float = 0.5,
             marge: float = 0.1, ratio: float = 3.0, frais_bps: float = 5.0) -> list[float]:
    """Résultats en R de chaque trade. Hypothèses prudentes : si le stop et l'objectif sont tous deux touchés
    dans la journée, on compte le stop ; si les deux niveaux d'entrée sont touchés, on retient celui qui est le
    plus proche de l'ouverture."""
    o, h, l, c = (df[k].to_numpy() for k in ("Open", "High", "Low", "Close"))
    a = atr(df).to_numpy()
    ok = filtre_jour(df, filtre).to_numpy()
    acheter, vendre = (s.to_numpy() for s in sens_autorise(df, tendance))
    frais = frais_bps / 10_000
    rs = []
    for i in range(1, len(df)):
        if not ok[i - 1] or not np.isfinite(a[i - 1]):
            continue
        n = niveaux(h[i - 1], l[i - 1], a[i - 1], k_stop, marge, ratio)
        touche_achat = acheter[i - 1] and h[i] >= n.achat
        touche_vente = vendre[i - 1] and l[i] <= n.vente
        if touche_achat and touche_vente:
            touche_achat = abs(o[i] - n.achat) <= abs(o[i] - n.vente)
            touche_vente = not touche_achat
        if touche_achat:
            entree = max(o[i], n.achat)
            risque = entree - n.achat_ko
            if l[i] <= n.achat_ko:
                sortie = n.achat_ko
            elif h[i] >= n.achat_objectif:
                sortie = n.achat_objectif
            else:
                sortie = c[i]
            rs.append((sortie - entree - frais * (entree + sortie)) / risque)
        elif touche_vente:
            entree = min(o[i], n.vente)
            risque = n.vente_ko - entree
            if h[i] >= n.vente_ko:
                sortie = n.vente_ko
            elif l[i] <= n.vente_objectif:
                sortie = n.vente_objectif
            else:
                sortie = c[i]
            rs.append((entree - sortie - frais * (entree + sortie)) / risque)
    return rs


def resume(rs: list[float]) -> dict:
    if not rs:
        return {"trades": 0}
    r = np.array(rs)
    g, p = r[r > 0], r[r < 0]
    return {"trades": len(r), "reussite_pct": round(100 * (r > 0).mean(), 1), "esperance_r": round(r.mean(), 3),
            "profit_factor": round(g.sum() / -p.sum(), 2) if len(p) else float("inf"),
            "r_total": round(r.sum(), 1)}
