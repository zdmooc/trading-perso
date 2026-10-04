"""Partie spéculation : les actions leaders du moment (force relative), achetées en actions réelles sur eToro.

Règle : chaque semaine, on classe les actions par leur hausse sur 6 mois comparée au S&P 500. On garde les
`nombre` premières, à condition qu'elles soient au-dessus de leur moyenne 50 jours. Une action est vendue
quand elle sort du classement élargi (2 × `nombre`) ou repasse sous sa moyenne 50 jours.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .indicators import sma

COLONNES = ["symbole", "nom", "rang", "force_relative_pct", "cours", "moyenne_50j"]


def classement(data: dict[str, pd.DataFrame], noms: dict[str, str], sp500: pd.DataFrame,
               jours: int = 126, min_jours: int = 50) -> pd.DataFrame:
    """Classement par force relative sur `jours` séances (ou depuis l'introduction si l'action est plus récente)."""
    sp = sp500["Close"]
    lignes = []
    for sym, df in data.items():
        c = df["Close"].dropna()
        if len(c) < min_jours:
            continue
        n = min(jours, len(c) - 1)
        debut = c.index[-n - 1]
        perf = c.iloc[-1] / c.iloc[-n - 1] - 1
        sp_debut = sp.asof(debut)
        perf_sp = sp.iloc[-1] / sp_debut - 1 if pd.notna(sp_debut) else 0.0
        mm50 = sma(c, 50).iloc[-1]
        lignes.append({"symbole": sym, "nom": noms.get(sym, sym), "force_relative_pct": round(100 * (perf - perf_sp), 1),
                       "cours": round(float(c.iloc[-1]), 2), "moyenne_50j": round(float(mm50), 2)})
    t = pd.DataFrame(lignes, columns=[c for c in COLONNES if c != "rang"])
    t = t.sort_values("force_relative_pct", ascending=False).reset_index(drop=True)
    t.insert(2, "rang", np.arange(1, len(t) + 1))
    return t


def selection(t: pd.DataFrame, precedente: list[str], nombre: int = 5) -> list[str]:
    """Garde les actions déjà détenues tant qu'elles restent dans le top 2 × nombre et au-dessus de la MM50,
    puis complète avec les meilleures du classement."""
    ok = t[t["cours"] > t["moyenne_50j"]]
    garde = [s for s in precedente if s in set(ok[ok["rang"] <= 2 * nombre]["symbole"])]
    for s in ok["symbole"]:
        if len(garde) >= nombre:
            break
        if s not in garde:
            garde.append(s)
    return garde


def charger(path: Path) -> list[str]:
    try:
        return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except FileNotFoundError:
        return []


def sauver(path: Path, symboles: list[str]) -> None:
    path.write_text("\n".join(symboles) + "\n", encoding="utf-8")


def rotation(data: dict[str, pd.DataFrame], sp500: pd.DataFrame, nombre: int = 5, jours: int = 126,
             frais_bps: float = 5.0, regime: pd.Series | None = None) -> pd.Series:
    """Backtest de la rotation hebdomadaire (parts égales, réajustées à chaque changement). Renvoie la courbe de capital.

    regime : si fourni, tout est vendu quand il est False (marché baissier).
    """
    prix = pd.DataFrame({s: df["Close"] for s, df in data.items()}).sort_index().ffill()
    prix = prix.loc[prix.index >= sp500.index[0]]
    rend = prix.pct_change().fillna(0.0)
    mm50 = prix.rolling(50).mean()
    perf = prix / prix.shift(jours) - 1
    sp = sp500["Close"].reindex(prix.index).ffill()
    rel = perf.sub(sp / sp.shift(jours) - 1, axis=0)
    vendredis = set(prix.index[prix.index.to_series().dt.weekday == 4])
    capital, detenus, courbe = 1.0, [], []
    for i, d in enumerate(prix.index):
        if detenus:
            capital *= 1 + rend.loc[d, detenus].mean()
        courbe.append(capital)
        if d not in vendredis or i < jours:
            continue
        if regime is not None and not bool(regime.asof(d)):
            nouveaux = []
        else:
            r = rel.loc[d].dropna().sort_values(ascending=False)
            t = pd.DataFrame({"symbole": r.index, "rang": np.arange(1, len(r) + 1),
                              "cours": prix.loc[d, r.index].values, "moyenne_50j": mm50.loc[d, r.index].values})
            nouveaux = selection(t, detenus, nombre)
        changes = len(set(nouveaux) ^ set(detenus))
        capital *= 1 - frais_bps / 10_000 * changes / max(nombre, 1)
        detenus = nouveaux
    return pd.Series(courbe, index=prix.index)


def to_markdown(t: pd.DataFrame, choisis: list[str], vendus: list[str], capital: float, seance) -> str:
    md = [f"# Spéculation : actions leaders (séance du {seance:%d/%m/%Y})\n",
          f"Capital spéculation : {capital:.0f} €, en parts égales, en **actions réelles sur eToro** (sans levier).\n",
          "Règle : les actions qui montent le plus par rapport au S&P 500 sur 6 mois, au-dessus de leur moyenne "
          "50 jours. Revue chaque semaine.\n",
          "## À détenir\n", "| Action | Rang | Force relative 6 mois | Cours | Moyenne 50 jours | Montant |",
          "| --- | --- | --- | --- | --- | --- |"]
    part = capital / max(len(choisis), 1)
    for s in choisis:
        r = t[t["symbole"] == s].iloc[0]
        md.append(f"| {r['nom']} | {r['rang']} | {r['force_relative_pct']:+} % | {r['cours']} | {r['moyenne_50j']} | {part:.0f} € |")
    if vendus:
        md.append("\n**À vendre** : " + ", ".join(t[t["symbole"].isin(vendus)]["nom"].tolist() or vendus) + ".\n")
    md += ["\n## Classement complet (15 premiers)\n", "| Rang | Action | Force relative 6 mois | Au-dessus de la MM50 |",
           "| --- | --- | --- | --- |"]
    for _, r in t.head(15).iterrows():
        md.append(f"| {r['rang']} | {r['nom']} | {r['force_relative_pct']:+} % | {'oui' if r['cours'] > r['moyenne_50j'] else 'non'} |")
    return "\n".join(md) + "\n"
