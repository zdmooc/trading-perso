"""Graphe daily d'un indice avec moyennes et zones d'achat (config.toml [zones]), vérification des zones,
archive datée et envoi Telegram. Usage : python scripts/graphe.py ^NDX"""
from __future__ import annotations

import csv
import sys
import tomllib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

from tradeperso import alerts


def etat_zone(jour: pd.Series, z: dict) -> str:
    """État d'une zone d'après la dernière bougie daily."""
    if jour["Close"] < z["stop"]:
        return "cassée" if jour["Low"] <= z["achat"] else "loin"
    if jour["Low"] <= z["achat"]:
        return "confirmée" if jour["Close"] > jour["Open"] else "touchée"
    return "en attente"


def main(symbole: str = "^NDX") -> None:
    cfg = tomllib.loads(Path("config.toml").read_text(encoding="utf-8")).get("zones", {}).get(symbole, {})
    zones = cfg.get("liste", [])
    df = yf.download(symbole, period="2y", interval="1d", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    c = df["Close"]
    jour, date = df.iloc[-1], df.index[-1]
    mm = {n: c.rolling(n).mean() for n in (20, 50, 200)}
    vue = c.tail(130)
    fig, ax = plt.subplots(figsize=(11, 6), dpi=110)
    ax.plot(vue.index, vue, color="#1f2937", lw=1.8, label=f"{symbole} {vue.iloc[-1]:,.0f}".replace(",", " "))
    for (n, s), col in zip(mm.items(), ["#2563eb", "#f59e0b", "#dc2626"]):
        ax.plot(vue.index, s.reindex(vue.index), color=col, lw=1, label=f"Moyenne {n} j {s.iloc[-1]:,.0f}".replace(",", " "))
    etats = []
    for z in zones:
        e = etat_zone(jour, z)
        etats.append((z, e))
        ax.axhspan(z["stop"], z["achat"], color="#16a34a", alpha=0.08)
        ax.axhline(z["achat"], color="#16a34a", lw=0.8, ls="--")
        ax.text(vue.index[2], z["achat"], f" {z['nom']} : achat {z['achat']:,} · stop {z['stop']:,} · {e}".replace(",", " "),
                va="bottom", fontsize=8, color="#166534")
    if cfg.get("invalidation"):
        ax.axhline(cfg["invalidation"], color="#dc2626", lw=0.8, ls=":")
    ax.set_title(f"{symbole} : zones d'achat sur repli (clôture du {date:%d/%m/%Y})")
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    nom = symbole.replace("^", "")
    dossier = Path("reports", "graphes")
    dossier.mkdir(parents=True, exist_ok=True)
    fig.savefig(Path("reports", f"graphe_{nom}.png"))            # dernier graphe
    fig.savefig(dossier / f"{nom}_{date:%Y-%m-%d}.png")          # archive datée
    # historique des vérifications
    histo = Path("reports", f"zones_{nom}.csv")
    neuf = not histo.exists()
    with histo.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if neuf:
            w.writerow(["date", "cloture", "plus_bas", "zone", "achat", "stop", "etat"])
        for z, e in etats:
            w.writerow([f"{date:%Y-%m-%d}", round(float(jour["Close"])), round(float(jour["Low"])), z["nom"], z["achat"], z["stop"], e])
    ecart = float(jour["Close"] - c.iloc[-2])
    lignes = [f"📈 <b>{symbole} {jour['Close']:,.0f}</b> ({ecart:+,.0f} pts)".replace(",", " ")]
    if cfg.get("invalidation") and jour["Close"] < cfg["invalidation"]:
        lignes.append(f"🚫 Sous {cfg['invalidation']:,} : tendance cassée, plus d'achat".replace(",", " "))
    for z, e in etats:
        icone = {"confirmée": "✅", "touchée": "👀", "cassée": "❌"}.get(e)
        if icone:
            lignes.append(f"{icone} {z['nom']} {e} (achat {z['achat']:,}, stop {z['stop']:,})".replace(",", " "))
    prochaine = next((z for z, e in etats if e == "en attente"), None)
    if len(lignes) == 1 and prochaine:
        lignes.append(f"Aucune zone touchée · la plus proche : {prochaine['achat']:,} ({prochaine['achat'] - jour['Close']:+,.0f} pts)".replace(",", " "))
    print("\n".join(lignes))
    alerts.send_photo(str(Path("reports", f"graphe_{nom}.png")), "\n".join(lignes))


if __name__ == "__main__":
    main(*sys.argv[1:])
