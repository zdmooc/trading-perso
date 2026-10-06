"""Où un indice peut finir l'année : statistiques historiques depuis la même date + contexte actuel.
Usage : python scripts/fin_annee.py ^NDX"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from tradeperso.indicators import rsi


def main(symbole: str = "^NDX") -> None:
    df = yf.download(symbole, period="max", interval="1d", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    c = df["Close"].dropna()
    dernier = c.index[-1]
    cours = float(c.iloc[-1])
    # performance de la même date jusqu'au 31/12, pour chaque année passée
    perfs = {}
    for an in sorted(set(c.index.year))[:-1]:
        s = c[c.index.year == an]
        depart = s[s.index.dayofyear >= dernier.dayofyear]
        if len(depart) > 20:
            perfs[an] = float(s.iloc[-1] / depart.iloc[0] - 1)
    p = pd.Series(perfs)
    vol = float(np.log(c).diff().tail(60).std() * np.sqrt(252))
    jours = int(np.busday_count(dernier.date(), pd.Timestamp(dernier.year, 12, 31).date()))
    sigma = vol * np.sqrt(jours / 252)
    mm50, mm200 = float(c.tail(50).mean()), float(c.tail(200).mean())
    debut_annee = float(c[c.index.year == dernier.year].iloc[0])
    haut = float(c.tail(252).max())
    lignes = [f"# {symbole} : fin d'année", "",
              f"Cours {cours:,.0f} le {dernier:%d/%m/%Y}, {jours} séances avant le 31/12.".replace(",", " "), "",
              "## Contexte", "",
              f"- Depuis le 1er janvier : {100 * (cours / debut_annee - 1):+.1f} % = {cours - debut_annee:+,.0f} pts".replace(",", " "),
              f"- Plus haut 1 an : {haut:,.0f} ({cours - haut:+,.0f} pts)".replace(",", " "),
              f"- Moyenne 50 j : {mm50:,.0f} ({cours - mm50:+,.0f} pts) · 200 j : {mm200:,.0f} ({cours - mm200:+,.0f} pts)".replace(",", " "),
              f"- RSI 14 daily : {float(rsi(c, 14).iloc[-1]):.0f} · volatilité 60 j : {100 * vol:.0f} % par an", "",
              f"## Historique : de cette date au 31/12 ({len(p)} années, {p.index.min()}-{p.index.max()})", "",
              f"- Années en hausse : {int((p > 0).sum())}/{len(p)} ({100 * (p > 0).mean():.0f} %)",
              f"- Moyenne {100 * p.mean():+.1f} % · médiane {100 * p.median():+.1f} %",
              f"- Pire {100 * p.min():+.1f} % ({p.idxmin()}) · meilleure {100 * p.max():+.1f} % ({p.idxmax()})",
              f"- 10 dernières années : " + ", ".join(f"{a} {100 * v:+.0f} %" for a, v in p.tail(10).items()), "",
              "## Fourchette au 31/12", "",
              "| Scénario | Variation | Niveau | Points |", "| --- | --- | --- | --- |"]
    for nom, q in [("Pessimiste (1 an sur 10)", 0.10), ("Prudent (1 an sur 4)", 0.25), ("Médian", 0.50),
                   ("Favorable (1 an sur 4)", 0.75), ("Très favorable (1 an sur 10)", 0.90)]:
        v = float(p.quantile(q))
        lignes.append(f"| {nom} | {100 * v:+.1f} % | {cours * (1 + v):,.0f} | {cours * v:+,.0f} |".replace(",", " "))
    lignes += ["", f"Selon la volatilité actuelle seule : 2 chances sur 3 entre {cours * np.exp(-sigma):,.0f} et "
               f"{cours * np.exp(sigma):,.0f}.".replace(",", " "), "", "Statistiques, pas une prédiction ni un conseil."]
    texte = "\n".join(lignes) + "\n"
    Path("reports", "fin_annee_" + symbole.replace("^", "") + ".md").write_text(texte, encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main(*sys.argv[1:])
