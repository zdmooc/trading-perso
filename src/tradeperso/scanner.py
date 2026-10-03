"""Détection des signaux du jour et calcul de la taille de position."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .strategies import STRATEGIES, TYPES, appliquer


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
    sens: int = 1  # 1 = achat, -1 = vente à découvert

    @property
    def type_trading(self) -> str:
        return TYPES.get(self.strategie, "swing")

    @property
    def risque_pct(self) -> float:
        return 100 * abs(self.entree - self.stop) / self.entree

    @property
    def ratio(self) -> float:
        """Ratio gain/perte : gain visé à l'objectif divisé par la perte au stop."""
        return abs(self.objectif - self.entree) / abs(self.entree - self.stop)


def scan(data: dict[str, pd.DataFrame], noms: dict[str, str], capital: float, risque: float,
         ratio_min: float = 0.0, regime: pd.Series | None = None, indices: set[str] | None = None,
         exclus: set[str] | None = None, places: int | None = None) -> list[Signal]:
    """Signaux de la dernière séance.

    regime : filtre de marché (achats seulement si True, ventes seulement si False).
    indices : symboles autorisés pour les stratégies réservées aux indices (ventes à découvert).
    exclus : symboles déjà en position ou en attente (un seul trade par actif).
    places : nombre maximum de nouveaux signaux (positions encore disponibles).
    """
    indices, exclus = indices or set(), exclus or set()
    meilleurs: dict[str, Signal] = {}
    for sym, df in data.items():
        if sym in exclus:
            continue
        for nom_strat, st in STRATEGIES.items():
            if st.indices_seulement and sym not in indices:
                continue
            last = appliquer(nom_strat, df, regime).iloc[-1]
            if not last["entry"] or not np.isfinite(last["stop"]):
                continue
            ecart = st.sens * (last["Close"] - last["stop"])
            if ecart <= 0:
                continue
            s = Signal(sym, noms.get(sym, sym), nom_strat, df.index[-1], float(last["Close"]),
                       float(last["stop"]), float(last["target"]), round(capital * risque / ecart, 2), st.sens)
            if s.ratio >= ratio_min - 1e-9 and (sym not in meilleurs or s.ratio > meilleurs[sym].ratio):
                meilleurs[sym] = s
    signaux = sorted(meilleurs.values(), key=lambda s: (-s.ratio, s.risque_pct))
    return signaux if places is None else signaux[:max(0, places)]


def to_markdown(signaux: list[Signal]) -> str:
    if not signaux:
        return "Aucun nouveau signal sur cette séance.\n"
    lignes = ["| Actif | Sens | Type | Stratégie | Clôture du signal | Cours (≈ entrée) | Stop | Objectif | Ratio gain/perte | Risque |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in signaux:
        lignes.append(f"| {s.nom} ({s.symbole}) | {'achat' if s.sens > 0 else 'vente'} | {s.type_trading} | "
                      f"{s.strategie} | {s.date:%Y-%m-%d} | {s.entree:.2f} | {s.stop:.2f} | {s.objectif:.2f} | "
                      f"{s.ratio:.1f} | {s.risque_pct:.1f} % |")
    return "\n".join(lignes) + "\n"
