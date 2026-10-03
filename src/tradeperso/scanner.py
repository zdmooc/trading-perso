"""Détection des signaux du jour et calcul de la taille de position."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .strategies import STRATEGIES


@dataclass
class Signal:
    symbole: str
    nom: str
    strategie: str
    date: pd.Timestamp
    entree: float
    stop: float
    objectif: float | None
    quantite: float

    @property
    def risque_pct(self) -> float:
        return 100 * (self.entree - self.stop) / self.entree


def scan(data: dict[str, pd.DataFrame], noms: dict[str, str], capital: float, risque: float) -> list[Signal]:
    signaux = []
    for sym, df in data.items():
        for nom_strat, strat in STRATEGIES.items():
            last = strat(df).iloc[-1]
            if not last["entry"] or not np.isfinite(last["stop"]) or last["stop"] >= last["Close"]:
                continue
            qte = capital * risque / (last["Close"] - last["stop"])
            objectif = float(last["target"]) if np.isfinite(last["target"]) else None
            signaux.append(Signal(sym, noms.get(sym, sym), nom_strat, df.index[-1],
                                  float(last["Close"]), float(last["stop"]), objectif, round(qte, 2)))
    return signaux


def to_markdown(signaux: list[Signal]) -> str:
    if not signaux:
        return "Aucun nouveau signal aujourd'hui.\n"
    lignes = ["| Actif | Stratégie | Date | Entrée (≈) | Stop | Objectif | Risque | Quantité |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in signaux:
        obj = f"{s.objectif:.2f}" if s.objectif else "sortie sur signal"
        lignes.append(f"| {s.nom} ({s.symbole}) | {s.strategie} | {s.date:%Y-%m-%d} | {s.entree:.2f} | "
                      f"{s.stop:.2f} | {obj} | {s.risque_pct:.1f} % | {s.quantite} |")
    return "\n".join(lignes) + "\n"
