"""Zones d'achat sur repli d'un indice : moyennes, anciens sommets, retracements, ATR, profondeur des replis passés.
Usage : python scripts/replis.py ^NDX"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

from tradeperso.indicators import atr


def main(symbole: str = "^NDX") -> None:
    df = yf.download(symbole, period="10y", interval="1d", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    c = df["Close"]
    cours = float(c.iloc[-1])
    a = float(atr(df, 14).iloc[-1])
    recent = df.tail(130)
    bas_i = recent["Low"].idxmin()
    bas = float(recent["Low"].min())
    haut = float(df.loc[bas_i:, "High"].max())
    niveaux = {
        "Moyenne 20 j": float(c.tail(20).mean()),
        "Moyenne 50 j": float(c.tail(50).mean()),
        "Moyenne 100 j": float(c.tail(100).mean()),
        "Moyenne 200 j": float(c.tail(200).mean()),
        f"Retracement 38,2 % (du bas {bas_i:%d/%m} au haut)": haut - 0.382 * (haut - bas),
        "Retracement 50 %": haut - 0.5 * (haut - bas),
        "Retracement 61,8 %": haut - 0.618 * (haut - bas),
        "Plus bas 1 mois": float(df.tail(21)["Low"].min()),
        "Plus bas 3 mois": float(df.tail(63)["Low"].min()),
    }
    # anciens sommets hebdo des 6 derniers mois (résistances devenues supports)
    hebdo = df["High"].resample("W").max().tail(26)
    for d, v in hebdo.nlargest(6).items():
        if v < cours * 0.995:
            niveaux[f"Ancien sommet semaine du {d:%d/%m}"] = float(v)
    # profondeur des replis en tendance haussière (cours au-dessus de la MM200) sur 10 ans
    mm200 = c.rolling(200).mean()
    plus_haut = c.cummax()
    repli = 1 - c / plus_haut
    en_tendance = c > mm200
    episodes, en_cours, prof = [], False, 0.0
    for r, t in zip(repli, en_tendance):
        if r > 0.02 and t:
            en_cours, prof = True, max(prof, r)
        elif r < 0.005 and en_cours:
            episodes.append(prof)
            en_cours, prof = False, 0.0
    ep = pd.Series(episodes)
    lignes = [f"# Zones d'achat sur repli : {symbole}", "",
              f"Cours {cours:,.0f} · ATR 14 j {a:,.0f} pts (mouvement moyen d'une journée)".replace(",", " "), "",
              "| Niveau | Cours | Distance |", "| --- | --- | --- |"]
    for nom, v in sorted(niveaux.items(), key=lambda x: -x[1]):
        lignes.append(f"| {nom} | {v:,.0f} | {v - cours:+,.0f} pts ({100 * (v / cours - 1):+.1f} %) |".replace(",", " "))
    if len(ep):
        lignes += ["", f"## Replis passés en tendance haussière (10 ans, {len(ep)} replis de plus de 2 %)", "",
                   f"- Médiane {100 * ep.median():.1f} % = {cours * ep.median():,.0f} pts".replace(",", " "),
                   f"- 3 replis sur 4 font moins de {100 * ep.quantile(0.75):.1f} % = {cours * ep.quantile(0.75):,.0f} pts".replace(",", " "),
                   f"- 9 sur 10 moins de {100 * ep.quantile(0.9):.1f} % = {cours * ep.quantile(0.9):,.0f} pts".replace(",", " ")]
    texte = "\n".join(lignes) + "\n\nStatistiques, pas un conseil.\n"
    Path("reports", "replis_" + symbole.replace("^", "") + ".md").write_text(texte, encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main(*sys.argv[1:])
