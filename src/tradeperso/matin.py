"""Plan de trading Europe : point du matin (7h), niveaux après la 1re heure (10h), bilan du soir (17h45).

Règle de journée testée sur données horaires : cassure de la 1re heure (9h-10h, heure de Paris).
- achat si le cours dépasse le plus haut de la 1re heure, vente s'il passe sous le plus bas ;
- un seul côté par jour (le premier touché) ;
- knock-out (stop) au milieu ou à l'autre bord de la 1re heure, objectif à 3 fois le risque ;
- tout est fermé à la dernière bougie de la séance.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .indicators import atr

PARIS = "Europe/Paris"
EUROPE = {"^GDAXI": "DAX 40", "^FCHI": "CAC 40", "^STOXX50E": "Euro Stoxx 50", "^FTSE": "FTSE 100"}
NUIT = {"ES=F": "S&P 500 (futures)", "NQ=F": "Nasdaq 100 (futures)", "^N225": "Nikkei 225", "^HSI": "Hang Seng",
        "BZ=F": "Pétrole Brent", "GC=F": "Or", "EURUSD=X": "Euro / dollar", "^VIX": "VIX (peur)"}
DEBUT, FIN = 9, 17  # bougies horaires de 9h à 17h (heure de Paris)


def telecharger(symboles, period: str, interval: str) -> dict[str, pd.DataFrame]:
    import yfinance as yf

    out = {}
    for s in symboles:
        try:
            df = yf.download(s, period=period, interval=interval, auto_adjust=True, progress=False, threads=False)
            if df.columns.nlevels > 1:
                df.columns = df.columns.get_level_values(0)
            df = df[["Open", "High", "Low", "Close"]].dropna()
            if len(df):
                if df.index.tz is not None:
                    df.index = df.index.tz_convert(PARIS)
                out[s] = df
        except Exception as e:  # une source manquante ne bloque pas le plan
            print(f"{s} : {e}")
    return out


def variation(df: pd.DataFrame) -> float:
    return 100 * (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) if len(df) >= 2 else float("nan")


def seance_du_jour(h: pd.DataFrame) -> pd.DataFrame:
    """Bougies horaires d'une séance européenne (9h à 17h, heure de Paris)."""
    return h[(h.index.hour >= DEBUT) & (h.index.hour <= FIN)]


def profil_horaire(h: pd.DataFrame) -> pd.Series:
    """Mouvement moyen (en %) de chaque bougie horaire, de l'ouverture à la clôture de la bougie."""
    s = seance_du_jour(h)
    mouv = (s["Close"] - s["Open"]).abs() / s["Open"] * 100
    return mouv.groupby(s.index.hour).mean()


@dataclass
class Jour:
    date: pd.Timestamp
    haut: float
    bas: float
    sens: int        # 1 achat, -1 vente, 0 aucun déclenchement
    entree: float
    stop: float
    objectif: float
    sortie: float
    r: float
    motif: str


def jouer(jour: pd.DataFrame, stop_mode: str = "milieu", ratio: float = 3.0, frais_bps: float = 2.0) -> Jour | None:
    """Rejoue une séance horaire avec la règle de la 1re heure. Hypothèse prudente : si le stop est touché dans
    la bougie d'entrée ou dans la même bougie que l'objectif, on compte le stop."""
    if len(jour) < 3 or jour.index[0].hour != DEBUT:
        return None
    haut, bas = float(jour["High"].iloc[0]), float(jour["Low"].iloc[0])
    milieu = (haut + bas) / 2
    reste = jour.iloc[1:]
    for i, (t, b) in enumerate(reste.iterrows()):
        up, down = b["High"] > haut, b["Low"] < bas
        if not (up or down):
            continue
        if up and down:
            sens = 1 if abs(b["Open"] - haut) <= abs(b["Open"] - bas) else -1
        else:
            sens = 1 if up else -1
        if sens > 0:
            entree = max(float(b["Open"]), haut)
            stop = milieu if stop_mode == "milieu" else bas
        else:
            entree = min(float(b["Open"]), bas)
            stop = milieu if stop_mode == "milieu" else haut
        risque = abs(entree - stop)
        if risque <= 0:
            return None
        objectif = entree + sens * ratio * risque
        sortie, motif = None, "clôture"
        for k, (_, c) in enumerate(reste.iloc[i:].iterrows()):
            touche_stop = c["Low"] <= stop if sens > 0 else c["High"] >= stop
            touche_obj = c["High"] >= objectif if sens > 0 else c["Low"] <= objectif
            if touche_stop:
                sortie, motif = stop, "stop"
                break
            if touche_obj and k > 0:
                sortie, motif = objectif, "objectif"
                break
        if sortie is None:
            sortie = float(reste["Close"].iloc[-1])
        frais = frais_bps / 10_000 * (entree + sortie)
        r = (sens * (sortie - entree) - frais) / risque
        return Jour(jour.index[0].normalize(), haut, bas, sens, entree, stop, objectif, sortie, r, motif)
    return Jour(jour.index[0].normalize(), haut, bas, 0, np.nan, np.nan, np.nan, np.nan, 0.0, "pas de cassure")


def backtest(h: pd.DataFrame, stop_mode: str = "milieu", ratio: float = 3.0, frais_bps: float = 2.0) -> list[Jour]:
    s = seance_du_jour(h)
    jours = [jouer(g, stop_mode, ratio, frais_bps) for _, g in s.groupby(s.index.date)]
    return [j for j in jours if j is not None and j.sens != 0]


def resume(jours: list[Jour]) -> dict:
    if not jours:
        return {"trades": 0}
    r = np.array([j.r for j in jours])
    g, p = r[r > 0], r[r < 0]
    return {"trades": len(r), "reussite_pct": round(100 * (r > 0).mean()), "esperance_r": round(float(r.mean()), 2),
            "profit_factor": round(g.sum() / -p.sum(), 2) if len(p) else float("inf")}


def pivots(d: pd.DataFrame) -> dict:
    h, l, c = (float(d[k].iloc[-1]) for k in ("High", "Low", "Close"))
    p = (h + l + c) / 3
    return {"pivot": p, "r1": 2 * p - l, "s1": 2 * p - h, "haut": h, "bas": l}


def journal_ajouter(path: Path, lignes: list[dict]) -> None:
    if not lignes:
        return
    nouveau = pd.DataFrame(lignes)
    if path.exists():
        ancien = pd.read_csv(path)
        nouveau = pd.concat([ancien, nouveau]).drop_duplicates(["date", "indice"], keep="last")
    nouveau.to_csv(path, index=False)
