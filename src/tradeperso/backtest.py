"""Backtest bougie par bougie : entrée à l'ouverture suivant le signal, stop et objectif intrajournaliers."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Trade:
    symbole: str
    entree_date: pd.Timestamp
    entree: float
    stop: float
    sortie_date: pd.Timestamp
    sortie: float
    motif: str

    @property
    def r(self) -> float:
        """Résultat en multiple du risque initial (R)."""
        return (self.sortie - self.entree) / (self.entree - self.stop)


def run(df: pd.DataFrame, symbole: str = "", frais_bps: float = 5.0) -> list[Trade]:
    """df doit contenir Open/High/Low/Close et les colonnes produites par une stratégie."""
    frais = frais_bps / 10_000
    trades: list[Trade] = []
    pos: dict | None = None
    o, h, l = df["Open"].to_numpy(), df["High"].to_numpy(), df["Low"].to_numpy()
    entry, exit_, stop, target = (df[c].to_numpy() for c in ("entry", "exit", "stop", "target"))
    idx = df.index

    for i in range(1, len(df)):
        if pos is None:
            if entry[i - 1] and np.isfinite(stop[i - 1]) and o[i] > stop[i - 1]:
                pos = {"date": idx[i], "prix": o[i] * (1 + frais), "stop": stop[i - 1], "target": target[i - 1]}
            else:
                continue
        # Position ouverte : sortie sur signal de la veille, stop, puis objectif.
        sortie = motif = None
        if exit_[i - 1] and idx[i] != pos["date"]:
            sortie, motif = o[i], "signal"
        elif l[i] <= pos["stop"]:
            sortie, motif = min(o[i], pos["stop"]), "stop"
        elif np.isfinite(pos["target"]) and h[i] >= pos["target"]:
            sortie, motif = max(o[i], pos["target"]), "objectif"
        if sortie is not None:
            trades.append(Trade(symbole, pos["date"], pos["prix"], pos["stop"], idx[i], sortie * (1 - frais), motif))
            pos = None
    return trades


def metrics(trades: list[Trade], risque: float = 0.01) -> dict:
    """Statistiques avec un risque fixe de `risque` du capital par trade (capital composé)."""
    if not trades:
        return {"trades": 0}
    rs = np.array([t.r for t in sorted(trades, key=lambda t: t.sortie_date)])
    equity = np.cumprod(1 + risque * rs)
    peak = np.maximum.accumulate(equity)
    gains, pertes = rs[rs > 0].sum(), -rs[rs < 0].sum()
    return {
        "trades": len(rs),
        "reussite_pct": round(100 * (rs > 0).mean(), 1),
        "r_moyen": round(rs.mean(), 2),
        "profit_factor": round(gains / pertes, 2) if pertes else float("inf"),
        "rendement_pct": round(100 * (equity[-1] - 1), 1),
        "drawdown_max_pct": round(100 * ((equity - peak) / peak).min(), 1),
    }
