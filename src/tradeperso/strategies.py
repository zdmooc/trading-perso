"""Stratégies swing (bougies journalières, positions acheteuses uniquement).

Chaque stratégie ajoute au DataFrame les colonnes :
- entry  : True si un signal d'achat apparaît à la clôture de la bougie (entrée à l'ouverture suivante)
- stop   : niveau de stop-loss associé au signal
- target : niveau d'objectif (sert aussi à calculer le ratio gain/perte)
- exit   : True si la règle de sortie est déclenchée à la clôture (sortie à l'ouverture suivante)
"""
from __future__ import annotations

from typing import Callable

import pandas as pd

from .indicators import atr, rsi, sma


def tendance_mm(df: pd.DataFrame) -> pd.DataFrame:
    """Croisement MM20/MM50 dans une tendance haussière (cours > MM200), objectif 3R."""
    out = df.copy()
    m20, m50, m200, a = sma(df["Close"], 20), sma(df["Close"], 50), sma(df["Close"], 200), atr(df)
    cross_up = (m20 > m50) & (m20.shift(1) <= m50.shift(1))
    cross_down = (m20 < m50) & (m20.shift(1) >= m50.shift(1))
    out["entry"] = cross_up & (df["Close"] > m200)
    out["stop"] = df["Close"] - 2 * a
    out["target"] = df["Close"] + 3 * (df["Close"] - out["stop"])
    out["exit"] = cross_down
    return out


def rsi2_repli(df: pd.DataFrame) -> pd.DataFrame:
    """Achat d'un repli (RSI 2 < 10) dans une tendance haussière, objectif 1,5 ATR, sortie au rebond (cours > MM5)."""
    out = df.copy()
    m5, m200, a = sma(df["Close"], 5), sma(df["Close"], 200), atr(df)
    out["entry"] = (rsi(df["Close"], 2) < 10) & (df["Close"] > m200)
    out["stop"] = df["Close"] - 2.5 * a
    out["target"] = df["Close"] + 1.5 * a
    out["exit"] = df["Close"] > m5
    return out


def cassure_20j(df: pd.DataFrame) -> pd.DataFrame:
    """Cassure du plus haut 20 jours (cours > MM200), objectif 3R, sortie sous le plus bas 10 jours."""
    out = df.copy()
    m200, a = sma(df["Close"], 200), atr(df)
    plus_haut = df["High"].rolling(20).max().shift(1)
    plus_bas = df["Low"].rolling(10).min().shift(1)
    out["entry"] = (df["Close"] > plus_haut) & (df["Close"] > m200)
    out["stop"] = df["Close"] - 2 * a
    out["target"] = df["Close"] + 3 * (df["Close"] - out["stop"])
    out["exit"] = df["Close"] < plus_bas
    return out


# Horizon de chaque stratégie : "swing" (bougies journalières, 2 à 15 jours) ou "day" (clôture le jour même).
TYPES = {"tendance_mm": "swing", "rsi2_repli": "swing", "cassure_20j": "swing"}

STRATEGIES: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    "tendance_mm": tendance_mm,
    "rsi2_repli": rsi2_repli,
    "cassure_20j": cassure_20j,
}
