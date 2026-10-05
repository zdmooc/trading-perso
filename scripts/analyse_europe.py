"""Analyse de fond du marché européen : tendance, momentum, largeur, secteurs. Écrit reports/analyse_europe.md."""
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

INDICES = {"^GDAXI": "DAX 40", "^FCHI": "CAC 40", "^STOXX50E": "Euro Stoxx 50", "^STOXX": "Stoxx 600",
           "^FTSE": "FTSE 100", "FTSEMIB.MI": "FTSE MIB", "^IBEX": "IBEX 35", "^AEX": "AEX", "^SSMI": "SMI"}
MACRO = {"EURUSD=X": "Euro/dollar", "BZ=F": "Brent", "GC=F": "Or", "^VIX": "VIX", "^GSPC": "S&P 500", "^TNX": "Taux US 10 ans"}
ACTIONS = {
    "Tech": ["ASML.AS", "SAP.DE", "PRX.AS", "IFX.DE", "CAP.PA"],
    "Banques": ["BNP.PA", "SAN.MC", "BBVA.MC", "INGA.AS", "UCG.MI", "ISP.MI", "DBK.DE", "GLE.PA"],
    "Assurance": ["ALV.DE", "CS.PA", "MUV2.DE", "ZURN.SW"],
    "Luxe et conso": ["MC.PA", "RMS.PA", "OR.PA", "KER.PA", "EL.PA", "ADS.DE", "ITX.MC"],
    "Industrie et défense": ["SIE.DE", "AIR.PA", "SAF.PA", "SU.PA", "RHM.DE", "DG.PA", "HO.PA"],
    "Auto": ["MBG.DE", "BMW.DE", "VOW3.DE", "STLAM.MI", "RNO.PA"],
    "Énergie et services publics": ["TTE.PA", "SHEL.L", "ENI.MI", "IBE.MC", "ENEL.MI", "ENGI.PA", "EOAN.DE"],
    "Santé": ["SAN.PA", "NOVN.SW", "ROG.SW", "AZN.L", "BAYN.DE", "NOVO-B.CO"],
    "Chimie et matériaux": ["BAS.DE", "AI.PA", "RIO.L", "GLEN.L"],
    "Télécoms": ["DTE.DE", "ORA.PA"],
}


def get(s, period="2y"):
    try:
        d = yf.download(s, period=period, progress=False, threads=False, auto_adjust=True)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        return d.dropna()
    except Exception:
        return pd.DataFrame()


def rsi(c, n=14):
    d = c.diff()
    g, p = d.clip(lower=0).ewm(alpha=1 / n).mean(), (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + g / p)


def perf(c, n):
    return 100 * (c.iloc[-1] / c.iloc[-1 - n] - 1) if len(c) > n else np.nan


def ligne(nom, d):
    c = d["Close"]
    tr = pd.concat([d["High"] - d["Low"], (d["High"] - c.shift()).abs(), (d["Low"] - c.shift()).abs()], axis=1).max(axis=1)
    ytd = c[c.index.year == c.index[-1].year]
    m50, m200 = c.rolling(50).mean().iloc[-1], c.rolling(200).mean().iloc[-1]
    return {"Indice": nom, "Cours": round(c.iloc[-1], 1), "1j %": perf(c, 1), "1 sem %": perf(c, 5), "1 mois %": perf(c, 21),
            "3 mois %": perf(c, 63), "Année %": 100 * (c.iloc[-1] / ytd.iloc[0] - 1),
            "vs MM50 %": 100 * (c.iloc[-1] / m50 - 1), "vs MM200 %": 100 * (c.iloc[-1] / m200 - 1),
            "RSI14": rsi(c).iloc[-1], "ATR %": 100 * tr.rolling(14).mean().iloc[-1] / c.iloc[-1],
            "Vol 20j %": c.pct_change().tail(20).std() * np.sqrt(252) * 100,
            "vs plus haut 1 an %": 100 * (c.iloc[-1] / c.tail(252).max() - 1)}


def table(rows):
    df = pd.DataFrame(rows).set_index(rows and list(rows[0])[0])
    return df.round(1).to_markdown()


out = []
rows = [ligne(n, d) for s, n in INDICES.items() if len(d := get(s)) > 210]
out += ["## Indices", table(rows)]
rows = [ligne(n, d) for s, n in MACRO.items() if len(d := get(s)) > 210]
out += ["## Contexte", table(rows)]

sect, largeur = [], {"MM50": 0, "MM200": 0, "n": 0}
for secteur, tick in ACTIONS.items():
    r = []
    for s in tick:
        d = get(s)
        if len(d) < 210:
            continue
        c = d["Close"]
        largeur["n"] += 1
        largeur["MM50"] += c.iloc[-1] > c.rolling(50).mean().iloc[-1]
        largeur["MM200"] += c.iloc[-1] > c.rolling(200).mean().iloc[-1]
        r.append({"Action": s, "1 mois %": perf(c, 21), "3 mois %": perf(c, 63), "vs MM200 %": 100 * (c.iloc[-1] / c.rolling(200).mean().iloc[-1] - 1)})
    if r:
        df = pd.DataFrame(r)
        best = df.sort_values("3 mois %").iloc[-1]
        worst = df.sort_values("3 mois %").iloc[0]
        sect.append({"Secteur": secteur, "1 mois %": df["1 mois %"].mean(), "3 mois %": df["3 mois %"].mean(),
                     "Au-dessus MM200": f"{int((df['vs MM200 %'] > 0).sum())}/{len(df)}",
                     "Meilleure (3 mois)": f"{best['Action']} {best['3 mois %']:+.0f} %",
                     "Pire (3 mois)": f"{worst['Action']} {worst['3 mois %']:+.0f} %"})
sect.sort(key=lambda x: -x["3 mois %"])
out += ["## Secteurs (moyenne des grandes valeurs)", pd.DataFrame(sect).set_index("Secteur").round(1).to_markdown(),
        f"\nLargeur : {largeur['MM50']}/{largeur['n']} actions au-dessus de la MM50, {largeur['MM200']}/{largeur['n']} au-dessus de la MM200."]

# saisonnalité octobre sur 20 ans pour DAX et CAC
for s, n in (("^GDAXI", "DAX 40"), ("^FCHI", "CAC 40")):
    d = get(s, "25y")
    if len(d):
        m = d["Close"].resample("ME").last().pct_change().dropna() * 100
        oc, nv = m[m.index.month == 10], m[m.index.month == 11]
        out.append(f"\n{n} : octobre positif {int((oc > 0).sum())}/{len(oc)} ans (moyenne {oc.mean():+.1f} %), "
                   f"novembre {int((nv > 0).sum())}/{len(nv)} (moyenne {nv.mean():+.1f} %).")

p = Path("reports/analyse_europe.md")
p.write_text(f"# Analyse du marché européen ({pd.Timestamp.now(tz='Europe/Paris'):%d/%m/%Y %H:%M})\n\n" + "\n\n".join(out) + "\n", encoding="utf-8")
print(p.read_text())
