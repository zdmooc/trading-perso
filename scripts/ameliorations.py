"""Test de 4 améliorations du plan du jour, sur l'historique horaire Yahoo. Usage : python scripts/ameliorations.py

1. Gap : pas d'entrée si l'ouverture a déjà dépassé le niveau de plus de la moitié du stop.
2. Stop à l'entrée : stop remonté au prix d'entrée dès +1 fois le risque.
3. Les deux ensemble.
4. Rebond technique : RSI 4 h sous le seuil + support hebdo (S1 ou S2) touché + bougie horaire de confirmation.
   Stop sous le plus bas des 3 dernières bougies, objectif à 3 fois le risque, sortie au plus tard après 16 bougies.
   Testé aussi dans l'autre sens (vente : RSI 4 h au-dessus de 100 - seuil, R1 ou R2 touché).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from tradeperso import matin, plan
from tradeperso.indicators import atr, rsi

VARIANTES = {"Règle actuelle": {}, "1. Sans gap": {"gap_max": 0.5}, "2. Stop à l'entrée à +1R": {"stop_entree": True},
             "3. Les deux": {"gap_max": 0.5, "stop_entree": True}}


def variantes(h, d, info, regle) -> dict[str, list[float]]:
    ses, ctx = plan.seances(h, info["heures"], info.get("debut_min", 0)), plan.contexte(d)
    jours = sorted(ses)
    res = {k: [] for k in VARIANTES}
    for veille, jour in zip(jours, jours[1:]):
        if veille not in ctx.index:
            continue
        g, c = ses[veille], ctx.loc[veille]
        liste = plan.ordres(regle, float(g["High"].max()), float(g["Low"].min()), float(c["atr"]), int(c["tendance"]))
        for nom, opts in VARIANTES.items():
            t = plan.rejouer(ses[jour], list(liste), info["fin_entree"], info["spread"], **opts)
            if t is not None:
                res[nom].append(t.pts)
    return res


def pivots_hebdo(d: pd.DataFrame) -> pd.DataFrame:
    """Pivots de la semaine précédente, valables pour chaque jour de la semaine en cours."""
    w = d.resample("W-FRI").agg({"High": "max", "Low": "min", "Close": "last"}).dropna()
    p = (w["High"] + w["Low"] + w["Close"]) / 3
    piv = pd.DataFrame({"S1": 2 * p - w["High"], "S2": p - (w["High"] - w["Low"]),
                        "R1": 2 * p - w["Low"], "R2": p + (w["High"] - w["Low"])}).shift(1)
    return piv.reindex(d.index, method="ffill")


def rebond(h, d, info, seuil: float, sens: int) -> list[float]:
    s = h.copy()
    idx_naif = s.index.tz_localize(None).normalize()
    r4 = rsi(s["Close"].resample("4h").last().dropna(), 14).shift(1)  # dernière bougie 4 h terminée
    s["rsi4"] = r4.reindex(s.index, method="ffill").to_numpy()
    dd = d.copy()
    dd.index = pd.DatetimeIndex(dd.index).tz_localize(None).normalize()
    piv = pivots_hebdo(dd)
    a = atr(dd).shift(1)
    s = s.join(piv.reindex(idx_naif).set_axis(s.index)).assign(atr=a.reindex(idx_naif).to_numpy()).dropna()
    o, hi, lo, c, r4v = (s[k].to_numpy() for k in ("Open", "High", "Low", "Close", "rsi4"))
    sup = s[["S1", "S2"]].to_numpy() if sens > 0 else s[["R1", "R2"]].to_numpy()
    av = s["atr"].to_numpy()
    pts, i, arme = [], 3, True
    while i < len(s):
        extreme = r4v[i] <= seuil if sens > 0 else r4v[i] >= 100 - seuil
        if not extreme:
            arme = True  # on attend la sortie de la zone extrême avant un nouveau trade
        if arme and extreme:
            fen = slice(i - 2, i + 1)
            if sens > 0:
                touche = (lo[fen].min() <= sup[i] + 0.1 * av[i]).any() and lo[fen].min() >= sup[i].min() - 0.5 * av[i]
                confirme = c[i] > hi[i - 1]
            else:
                touche = (hi[fen].max() >= sup[i] - 0.1 * av[i]).any() and hi[fen].max() <= sup[i].max() + 0.5 * av[i]
                confirme = c[i] < lo[i - 1]
            if touche and confirme:
                entree = c[i]
                stop = (lo[fen].min() - 0.05 * av[i]) if sens > 0 else (hi[fen].max() + 0.05 * av[i])
                risque = abs(entree - stop)
                obj = entree + sens * 3 * risque
                sortie, j = None, i + 1
                while j < len(s) and j <= i + 16:
                    if (lo[j] <= stop) if sens > 0 else (hi[j] >= stop):
                        sortie = stop
                        break
                    if (hi[j] >= obj) if sens > 0 else (lo[j] <= obj):
                        sortie = obj
                        break
                    j += 1
                if sortie is None:
                    j = min(j, len(s) - 1)
                    sortie = c[j]
                pts.append(sens * (sortie - entree) - info["spread"])
                arme, i = False, j + 1
                continue
        i += 1
    return pts


def ligne(nom: str, pts: list[float], taille: float) -> str:
    s = plan.stats(pts, taille)
    if not s.get("trades"):
        return f"| {nom} | 0 | | | | | |"
    return (f"| {nom} | {s['trades']} | {s['gagnes_pct']} % | {plan.pts(s['gain_moy'])} | {s['perdus_pct']} % | "
            f"{plan.pts(s['perte_moy'])} | {plan.pts(s['total_pts'])} = {plan.eur(s['total_eur'])} |")


def main() -> None:
    d = matin.telecharger(plan.INDICES, "5y", "1d")
    h = matin.telecharger(plan.INDICES, "730d", "1h")
    st = json.loads(Path("reports/plan/stats.json").read_text(encoding="utf-8"))
    md = ["# Améliorations testées sur le plan du jour", "",
          f"Bougies horaires Yahoo depuis le {min(x.index[0] for x in h.values()).date()}. Points nets du spread IG.", ""]
    for s, info in plan.INDICES.items():
        if s not in h or s not in d:
            continue
        regle = plan.PAR_CLE[st["indices"][s]["choisie"]]
        md += [f"## {info['nom']} ({info['taille']:g} contrat)".replace(".", ","), "", f"Règle actuelle : {regle.nom}.", "",
               "| Variante | Trades | Gagnés | Gain moyen | Perdus | Perte moyenne | Total |",
               "| --- | --- | --- | --- | --- | --- | --- |"]
        for nom, p in variantes(h[s], d[s], info, regle).items():
            md.append(ligne(nom, p, info["taille"]))
        for seuil in (30, 35):
            md.append(ligne(f"4. Rebond technique achat (RSI 4 h ≤ {seuil})", rebond(h[s], d[s], info, seuil, 1), info["taille"]))
            md.append(ligne(f"4. Rebond technique vente (RSI 4 h ≥ {100 - seuil})", rebond(h[s], d[s], info, seuil, -1), info["taille"]))
        md.append("")
    texte = "\n".join(md) + "\n"
    Path("reports/ameliorations.md").write_text(texte, encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main()
