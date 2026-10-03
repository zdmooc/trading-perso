"""Backtest « portefeuille » : mêmes règles que le scan réel (positions limitées, une par actif, risque fixe)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import backtest
from .strategies import STRATEGIES, appliquer, regime_haussier


@dataclass
class Candidat:
    strategie: str
    trade: backtest.Trade


def candidats(data: dict[str, pd.DataFrame], indices: set[str], frais_bps: float, ratio_min: float = 0.0,
              filtre_marche: bool = True, breakeven_r: float | None = None, sp500: str = "^GSPC",
              **reglages) -> list[Candidat]:
    """Tous les trades possibles des stratégies actives, avec les filtres du scan."""
    lent = reglages.get("lent", 200)
    regime = regime_haussier(data[sp500], lent) if filtre_marche and sp500 in data else None
    out = []
    for nom, st in STRATEGIES.items():
        if not st.actif:
            continue
        for sym, df in data.items():
            if st.indices_seulement and sym not in indices:
                continue
            s = appliquer(nom, df, regime, **reglages)
            if ratio_min:  # même filtre que le scan : ratio gain/perte du signal
                ratio = (s["target"] - s["Close"]).abs() / (s["Close"] - s["stop"]).abs()
                s["entry"] = s["entry"] & (ratio >= ratio_min - 1e-9)
            out += [Candidat(nom, t) for t in backtest.run(s, sym, frais_bps, st.sens, breakeven_r)]
    return out


def simuler(cands: list[Candidat], max_positions: int = 4, risque: float = 0.01) -> dict:
    """Rejoue les trades dans l'ordre chronologique en respectant la limite de positions.

    Une position libère sa place le jour de sa sortie ; un nouveau trade n'entre qu'à une date ultérieure
    (le scan du soir voit la clôture, l'entrée a lieu à l'ouverture suivante). Le risque est de `risque`
    du capital au moment de l'entrée.
    """
    cands = sorted(cands, key=lambda c: (c.trade.entree_date, c.trade.symbole, c.strategie))
    capital, ouverts, pris, courbe = 1.0, [], [], []

    def fermer_avant(date):
        nonlocal capital
        for pos in sorted([p for p in ouverts if p[0].trade.sortie_date < date], key=lambda p: p[0].trade.sortie_date):
            capital += pos[1] * pos[0].trade.r
            courbe.append((pos[0].trade.sortie_date, capital))
            ouverts.remove(pos)

    for c in cands:
        fermer_avant(c.trade.entree_date)
        if len(ouverts) >= max_positions or any(p[0].trade.symbole == c.trade.symbole for p in ouverts):
            continue
        ouverts.append((c, capital * risque))
        pris.append(c)
    fermer_avant(pd.Timestamp.max)
    return mesures(pris, courbe)


def mesures(pris: list[Candidat], courbe: list[tuple]) -> dict:
    if not pris:
        return {"trades": 0}
    rs = np.array([c.trade.r for c in pris])
    eq = pd.Series([v for _, v in courbe], index=[d for d, _ in courbe])
    pic = eq.cummax()
    dd = (eq - pic) / pic
    # Durée de la plus longue période sous un ancien sommet.
    sous, debut, plus_long = dd < 0, None, pd.Timedelta(0)
    for d, s in sous.items():
        if s and debut is None:
            debut = d
        elif not s and debut is not None:
            plus_long, debut = max(plus_long, d - debut), None
    if debut is not None:
        plus_long = max(plus_long, eq.index[-1] - debut)
    annees = max((eq.index[-1] - pris[0].trade.entree_date).days / 365.25, 1e-9)
    gains, pertes = rs[rs > 0], rs[rs < 0]
    return {
        "trades": len(rs),
        "reussite_pct": round(100 * (rs > 0).mean(), 1),
        "gain_moyen_r": round(gains.mean(), 2) if len(gains) else 0.0,
        "perte_moyenne_r": round(pertes.mean(), 2) if len(pertes) else 0.0,
        "esperance_r": round(rs.mean(), 2),
        "profit_factor": round(gains.sum() / -pertes.sum(), 2) if len(pertes) else float("inf"),
        "rendement_annuel_pct": round(100 * (eq.iloc[-1] ** (1 / annees) - 1), 1),
        "rendement_total_pct": round(100 * (eq.iloc[-1] - 1), 1),
        "drawdown_max_pct": round(100 * dd.min(), 1),
        "drawdown_duree_mois": round(plus_long.days / 30.44, 1),
        "par_strategie": {s: (int(n), round(float(r), 1)) for s, (n, r) in
                          pd.DataFrame({"s": [c.strategie for c in pris], "r": rs}).groupby("s")["r"]
                          .agg(["count", "sum"]).iterrows()},
    }
