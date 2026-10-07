"""Devises : quelles monnaies sont trop haussières ou trop baissières. Usage : python scripts/devises.py

Pour chaque grande paire : RSI 14 en daily et en hebdo, écart à la moyenne 50 jours, variation sur 1 mois en pips.
Force de chaque monnaie : moyenne de sa variation sur 1 mois contre les 7 autres.
"""
from __future__ import annotations

import itertools
import os
from pathlib import Path

import pandas as pd
import yfinance as yf

from tradeperso import alerts
from tradeperso.indicators import rsi

MONNAIES = ["USD", "EUR", "JPY", "GBP", "CHF", "AUD", "CAD", "NZD"]
NOMS = {"USD": "dollar US", "EUR": "euro", "JPY": "yen", "GBP": "livre", "CHF": "franc suisse", "AUD": "dollar australien",
        "CAD": "dollar canadien", "NZD": "dollar néo-zélandais"}
PAIRES = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "EURJPY", "EURGBP", "EURCHF", "GBPJPY",
          "AUDJPY"]


def pip(paire: str) -> float:
    return 0.01 if paire.endswith("JPY") else 0.0001


def charger(paire: str, intervalle: str, periode: str) -> pd.Series:
    df = yf.download(paire + "=X", period=periode, interval=intervalle, auto_adjust=True, progress=False, threads=False)
    if df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)
    return df["Close"].dropna()


def etat(rd: float, rh: float) -> str:
    if rd >= 70 or rh >= 70:
        return "🔥 trop haussière"
    if rd <= 30 or rh <= 30:
        return "🧊 trop baissière"
    if rd >= 60:
        return "↗ haussière"
    if rd <= 40:
        return "↘ baissière"
    return "neutre"


def main() -> None:
    lignes, var1m = [], {}
    for p in PAIRES:
        try:
            d, w = charger(p, "1d", "1y"), charger(p, "1wk", "5y")
        except Exception as e:
            print(p, e)
            continue
        if len(d) < 60:
            continue
        c = float(d.iloc[-1])
        rd, rh = float(rsi(d, 14).iloc[-1]), float(rsi(w, 14).iloc[-1])
        mm50 = float(d.rolling(50).mean().iloc[-1])
        un_mois = float(d.iloc[-22]) if len(d) > 22 else float(d.iloc[0])
        var1m[p] = 100 * (c / un_mois - 1)
        lignes.append(dict(paire=p, cours=c, rsi_d=rd, rsi_h=rh, ecart_mm50=(c - mm50) / pip(p),
                           var_1m=(c - un_mois) / pip(p), var_1m_pct=var1m[p], etat=etat(rd, rh)))
    t = pd.DataFrame(lignes)
    # Force des monnaies : variation 1 mois de chaque monnaie contre les autres (paires croisées via le dollar).
    usd = {"USD": 0.0}
    for p, v in var1m.items():
        if p.endswith("USD"):
            usd[p[:3]] = v
        elif p.startswith("USD"):
            usd[p[3:]] = -v
    force = {m: sum(usd[m] - usd[o] for o in usd if o != m) / (len(usd) - 1) for m in usd}
    force = dict(sorted(force.items(), key=lambda x: -x[1]))

    md = ["# Devises : surchauffe et force des monnaies", "",
          f"Calculé le {pd.Timestamp.now(tz='Europe/Paris'):%d/%m/%Y à %Hh%M}. 1 pip = 0,0001 (0,01 pour le yen).", "",
          "Trop haussière = RSI 14 au-dessus de 70 (daily ou hebdo). Trop baissière = sous 30.", "",
          "| Paire | Cours | RSI daily | RSI hebdo | Écart à la MM50 | 1 mois | État |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in t.sort_values("rsi_d", ascending=False).itertuples():
        md.append(f"| {r.paire} | {r.cours:.4f} | {r.rsi_d:.0f} | {r.rsi_h:.0f} | {r.ecart_mm50:+.0f} pips | "
                  f"{r.var_1m_pct:+.1f} % = {r.var_1m:+.0f} pips | {r.etat} |")
    md += ["", "## Force des monnaies sur 1 mois", "", "| Monnaie | Force |", "| --- | --- |"]
    md += [f"| {NOMS[m]} ({m}) | {v:+.1f} % |" for m, v in force.items()]
    Path("reports").mkdir(exist_ok=True)
    texte = "\n".join(md) + "\n"
    Path("reports/devises.md").write_text(texte, encoding="utf-8")
    print(texte)
    if os.environ.get("TELEGRAM_TOKEN"):
        fortes, faibles = list(force)[:2], list(force)[-2:]
        msg = ["💱 <b>Devises</b>", "", f"💪 Plus fortes : {', '.join(NOMS[m] for m in fortes)}",
               f"🥀 Plus faibles : {', '.join(NOMS[m] for m in faibles)}"]
        for r in t.itertuples():
            if "trop" in r.etat:
                msg += ["", f"{r.etat} {r.paire} {r.cours:.4f} · RSI {r.rsi_d:.0f} · 1 mois {r.var_1m:+.0f} pips"]
        alerts.send_telegram(["\n".join(msg)])


if __name__ == "__main__":
    main()
