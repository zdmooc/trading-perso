"""Divergences RSI (14) d'un indice en mensuel, hebdo et daily. Usage : python scripts/divergence.py ^NDX"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

from tradeperso.indicators import rsi

UNITES = {"Mensuel": ("1mo", "max", 3, 36), "Hebdo": ("1wk", "10y", 4, 52), "Daily": ("1d", "2y", 5, 120)}


def sommets(close: pd.Series, k: int) -> list[int]:
    """Positions des plus hauts locaux (plus haut sur k bougies de chaque côté)."""
    v = close.values
    return [i for i in range(k, len(v) - k) if v[i] == max(v[i - k:i + k + 1])]


def creux(close: pd.Series, k: int) -> list[int]:
    v = close.values
    return [i for i in range(k, len(v) - k) if v[i] == min(v[i - k:i + k + 1])]


def analyser(df: pd.DataFrame, k: int, fenetre: int) -> dict:
    c = df["Close"].dropna()
    r = rsi(c, 14)
    debut = len(c) - fenetre
    hauts = [i for i in sommets(c, k) if i >= debut]
    bas = [i for i in creux(c, k) if i >= debut]
    # la dernière bougie compte comme sommet si elle est au plus haut des k dernières
    n = len(c) - 1
    if c.iloc[n] >= c.iloc[-k - 1:].max() and (not hauts or hauts[-1] < n - k):
        hauts.append(n)
    if c.iloc[n] <= c.iloc[-k - 1:].min() and (not bas or bas[-1] < n - k):
        bas.append(n)
    res = {"cours": c.iloc[-1], "rsi": r.iloc[-1], "baissiere": None, "haussiere": None}
    if len(hauts) >= 2:
        a, b = hauts[-2], hauts[-1]
        res["h"] = (c.index[a], c.iloc[a], r.iloc[a], c.index[b], c.iloc[b], r.iloc[b])
        res["baissiere"] = bool(c.iloc[b] > c.iloc[a] and r.iloc[b] < r.iloc[a])
    if len(bas) >= 2:
        a, b = bas[-2], bas[-1]
        res["haussiere"] = bool(c.iloc[b] < c.iloc[a] and r.iloc[b] > r.iloc[a])
    return res


def main(symbole: str = "^NDX") -> None:
    lignes = [f"# Divergences RSI 14 : {symbole}", "",
              f"Calculé le {pd.Timestamp.now(tz='Europe/Paris'):%d/%m/%Y %Hh%M} (Paris), clôtures Yahoo.", "",
              "| Unité | Cours | RSI | Sommet précédent | Dernier sommet | Divergence baissière |",
              "| --- | --- | --- | --- | --- | --- |"]
    for nom, (iv, per, k, fen) in UNITES.items():
        df = yf.download(symbole, period=per, interval=iv, auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        x = analyser(df, k, fen)
        if "h" in x:
            da, pa, ra, db, pb, rb = x["h"]
            prec = f"{da:%d/%m/%Y} : {pa:,.0f} (RSI {ra:.1f})".replace(",", " ")
            dern = f"{db:%d/%m/%Y} : {pb:,.0f} (RSI {rb:.1f}), {pb - pa:+,.0f} pts".replace(",", " ")
        else:
            prec = dern = "-"
        verdict = "🔴 OUI" if x["baissiere"] else ("non" if x["baissiere"] is False else "?")
        lignes.append(f"| {nom} | {x['cours']:,.0f} | {x['rsi']:.0f} | {prec} | {dern} | {verdict} |".replace(",", " "))
    lignes += ["", "Divergence baissière = le cours fait un plus haut plus haut, mais le RSI fait un plus haut plus bas.",
               "Simulation, pas un conseil."]
    texte = "\n".join(lignes) + "\n"
    nom_fichier = "divergence_" + symbole.replace("^", "").replace("=", "") + ".md"
    Path("reports").mkdir(exist_ok=True)
    Path("reports", nom_fichier).write_text(texte, encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main(*sys.argv[1:])
