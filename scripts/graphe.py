"""Graphe daily d'un indice avec moyennes et zones d'achat sur repli, envoyé sur Telegram.
Usage : python scripts/graphe.py ^NDX"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

from tradeperso import alerts

ZONES = {"^NDX": [(30700, 30200, "Zone 1"), (29950, 29400, "Zone 2 (meilleure)"), (29500, 28950, "Zone 3"),
                  (28750, 28100, "Zone 4")]}


def main(symbole: str = "^NDX") -> None:
    df = yf.download(symbole, period="2y", interval="1d", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    c = df["Close"]
    mm = {n: c.rolling(n).mean() for n in (20, 50, 200)}
    vue = c.tail(130)
    fig, ax = plt.subplots(figsize=(11, 6), dpi=110)
    ax.plot(vue.index, vue, color="#1f2937", lw=1.8, label=f"{symbole} {vue.iloc[-1]:,.0f}".replace(",", " "))
    for (n, s), col in zip(mm.items(), ["#2563eb", "#f59e0b", "#dc2626"]):
        ax.plot(vue.index, s.reindex(vue.index), color=col, lw=1, label=f"Moyenne {n} j {s.iloc[-1]:,.0f}".replace(",", " "))
    for achat, stop, nom in ZONES.get(symbole, []):
        ax.axhspan(stop, achat, color="#16a34a", alpha=0.08)
        ax.axhline(achat, color="#16a34a", lw=0.8, ls="--")
        ax.text(vue.index[2], achat, f" {nom} : achat {achat:,} · stop {stop:,}".replace(",", " "),
                va="bottom", fontsize=8, color="#166534")
    ax.set_title(f"{symbole} : zones d'achat sur repli ({pd.Timestamp.now():%d/%m/%Y})")
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    chemin = Path("reports", "graphe_" + symbole.replace("^", "") + ".png")
    fig.savefig(chemin)
    print(chemin)
    alerts.send_photo(str(chemin), f"📈 <b>{symbole}</b> : zones d'achat sur repli")


if __name__ == "__main__":
    main(*sys.argv[1:])
