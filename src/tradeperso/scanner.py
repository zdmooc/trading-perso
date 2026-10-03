"""Détection des signaux du jour et calcul de la taille de position."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .strategies import STRATEGIES, TYPES


@dataclass
class Signal:
    symbole: str
    nom: str
    strategie: str
    date: pd.Timestamp
    entree: float
    stop: float
    objectif: float
    quantite: float

    @property
    def type_trading(self) -> str:
        return TYPES.get(self.strategie, "swing")

    @property
    def risque_pct(self) -> float:
        return 100 * (self.entree - self.stop) / self.entree

    @property
    def ratio(self) -> float:
        """Ratio gain/perte : gain visé à l'objectif divisé par la perte au stop."""
        return (self.objectif - self.entree) / (self.entree - self.stop)


def scan(data: dict[str, pd.DataFrame], noms: dict[str, str], capital: float, risque: float) -> list[Signal]:
    signaux = []
    for sym, df in data.items():
        for nom_strat, strat in STRATEGIES.items():
            last = strat(df).iloc[-1]
            if not last["entry"] or not np.isfinite(last["stop"]) or last["stop"] >= last["Close"]:
                continue
            qte = capital * risque / (last["Close"] - last["stop"])
            signaux.append(Signal(sym, noms.get(sym, sym), nom_strat, df.index[-1], float(last["Close"]),
                                  float(last["stop"]), float(last["target"]), round(qte, 2)))
    return signaux


def to_markdown(signaux: list[Signal]) -> str:
    if not signaux:
        return "Aucun nouveau signal sur cette séance.\n"
    lignes = ["| Actif | Type | Stratégie | Clôture du signal | Cours (≈ entrée) | Stop | Objectif | Ratio gain/perte | Risque |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in signaux:
        lignes.append(f"| {s.nom} ({s.symbole}) | {s.type_trading} | {s.strategie} | {s.date:%Y-%m-%d} | "
                      f"{s.entree:.2f} | {s.stop:.2f} | {s.objectif:.2f} | {s.ratio:.1f} | "
                      f"{s.risque_pct:.1f} % |")
    return "\n".join(lignes) + "\n"
