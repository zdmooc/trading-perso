"""Stratégies swing (bougies journalières), à l'achat et à la vente.

Chaque stratégie ajoute au DataFrame les colonnes :
- entry  : True si un signal apparaît à la clôture de la bougie (entrée à l'ouverture suivante)
- stop   : niveau de stop-loss associé au signal
- target : niveau d'objectif (sert aussi à calculer le ratio gain/perte)
- exit   : True si la règle de sortie est déclenchée à la clôture (sortie à l'ouverture suivante)
"""
from __future__ import annotations

from dataclasses import dataclass
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


def tendance_mm_vente(df: pd.DataFrame) -> pd.DataFrame:
    """Croisement MM20 sous MM50 dans une tendance baissière (cours < MM200), objectif 3R."""
    out = df.copy()
    m20, m50, m200, a = sma(df["Close"], 20), sma(df["Close"], 50), sma(df["Close"], 200), atr(df)
    cross_up = (m20 > m50) & (m20.shift(1) <= m50.shift(1))
    cross_down = (m20 < m50) & (m20.shift(1) >= m50.shift(1))
    out["entry"] = cross_down & (df["Close"] < m200)
    out["stop"] = df["Close"] + 2 * a
    out["target"] = df["Close"] - 3 * (out["stop"] - df["Close"])
    out["exit"] = cross_up
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


def cassure_20j_vente(df: pd.DataFrame) -> pd.DataFrame:
    """Cassure du plus bas 20 jours (cours < MM200), objectif 3R, sortie au-dessus du plus haut 10 jours."""
    out = df.copy()
    m200, a = sma(df["Close"], 200), atr(df)
    plus_bas = df["Low"].rolling(20).min().shift(1)
    plus_haut = df["High"].rolling(10).max().shift(1)
    out["entry"] = (df["Close"] < plus_bas) & (df["Close"] < m200)
    out["stop"] = df["Close"] + 2 * a
    out["target"] = df["Close"] - 3 * (out["stop"] - df["Close"])
    out["exit"] = df["Close"] > plus_haut
    return out


def _repli(df: pd.DataFrame, sens: int, objectif_r: float) -> pd.DataFrame:
    """Repli dans une tendance établie, entrée sur reprise confirmée, stop sous le creux du repli."""
    out = df.copy()
    c = df["Close"] * sens
    haut, bas = (df["High"], df["Low"]) if sens > 0 else (-df["Low"], -df["High"])
    m20, m50, m200, a = sma(c, 20), sma(c, 50), sma(c, 200), atr(df)
    tendance = (c > m50) & (m50 > m200) & (m50 > m50.shift(5))
    repli = (bas <= m20).rolling(5).max().astype(bool)          # le cours est revenu toucher la MM20
    reprise = (c > haut.shift(1)) & (c > m20)                    # clôture au-dessus du plus haut de la veille
    creux = bas.rolling(5).min() - 0.25 * a
    risque = (c - creux).clip(lower=0.5 * a)                     # stop au moins à 0,5 ATR
    out["entry"] = tendance & repli & reprise
    out["stop"] = (c - risque) * sens
    out["target"] = (c + objectif_r * risque) * sens
    out["exit"] = c < m50
    return out


def repli_tendance(df: pd.DataFrame) -> pd.DataFrame:
    """Achat d'un repli sur la MM20 dans une tendance haussière, objectif 3R, sortie sous la MM50."""
    return _repli(df, 1, 3.0)


def repli_tendance_2r(df: pd.DataFrame) -> pd.DataFrame:
    """Même règle avec un objectif à 2R (comparaison seulement)."""
    return _repli(df, 1, 2.0)


def repli_tendance_vente(df: pd.DataFrame) -> pd.DataFrame:
    """Vente d'un rebond sur la MM20 dans une tendance baissière, objectif 3R, sortie au-dessus de la MM50."""
    return _repli(df, -1, 3.0)


@dataclass(frozen=True)
class Strategie:
    fonction: Callable[[pd.DataFrame], pd.DataFrame]
    sens: int            # 1 = achat, -1 = vente à découvert
    type: str = "swing"  # "swing" (bougies journalières, 2 à 15 jours) ou "day" (clôture le jour même)
    indices_seulement: bool = False
    actif: bool = True   # False : présent dans le backtest seulement, aucun signal envoyé


STRATEGIES: dict[str, Strategie] = {
    "tendance_mm": Strategie(tendance_mm, 1),
    "rsi2_repli": Strategie(rsi2_repli, 1),
    "cassure_20j": Strategie(cassure_20j, 1),
    # Ventes à découvert : indices uniquement (CFD sur IG et eToro).
    "tendance_mm_vente": Strategie(tendance_mm_vente, -1, indices_seulement=True),
    "cassure_20j_vente": Strategie(cassure_20j_vente, -1, indices_seulement=True),
    # En test (backtest seulement) : repli dans la tendance.
    "repli_tendance": Strategie(repli_tendance, 1, actif=False),
    "repli_tendance_2r": Strategie(repli_tendance_2r, 1, actif=False),
    "repli_tendance_vente": Strategie(repli_tendance_vente, -1, indices_seulement=True, actif=False),
}
TYPES = {nom: s.type for nom, s in STRATEGIES.items()}


def regime_haussier(sp500: pd.DataFrame) -> pd.Series:
    """True quand le S&P 500 clôture au-dessus de sa moyenne mobile 200 jours."""
    return sp500["Close"] > sma(sp500["Close"], 200)


def appliquer(nom: str, df: pd.DataFrame, regime: pd.Series | None = None) -> pd.DataFrame:
    """Calcule la stratégie ; avec un régime de marché, n'achète qu'en marché haussier et ne vend qu'en marché baissier."""
    st = STRATEGIES[nom]
    out = st.fonction(df)
    if regime is not None:
        r = regime.reindex(out.index, method="ffill").fillna(False).astype(bool)
        out["entry"] = out["entry"] & (r if st.sens > 0 else ~r)
    return out
