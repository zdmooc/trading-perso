"""Chargement des données (Yahoo Finance) et de la configuration."""
from __future__ import annotations

import tomllib
from pathlib import Path

import pandas as pd


def load_config(path: str | Path = "config.toml") -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def watchlist(cfg: dict) -> dict[str, str]:
    return {**cfg.get("indices", {}), **cfg.get("actions_us", {})}


def download(symboles: list[str], period: str = "10y") -> dict[str, pd.DataFrame]:
    """Bougies journalières ajustées, une table OHLC par symbole."""
    import yfinance as yf

    raw = yf.download(symboles, period=period, interval="1d", auto_adjust=True,
                      group_by="ticker", progress=False, threads=False)
    out = {}
    for s in symboles:
        df = raw[s] if raw.columns.nlevels > 1 else raw
        df = df[["Open", "High", "Low", "Close"]].dropna()
        if len(df) > 0:
            out[s] = df
    return out


def prochains_resultats(symbole: str):
    """Date de la prochaine publication de résultats (Yahoo), ou None si inconnue."""
    import yfinance as yf

    try:
        cal = yf.Ticker(symbole).calendar or {}
        dates = cal.get("Earnings Date") or []
        futures = sorted(pd.Timestamp(d).date() for d in dates if pd.Timestamp(d).date() >= pd.Timestamp.today().date())
        return futures[0] if futures else None
    except Exception:
        return None


def fraicheur(data: dict[str, pd.DataFrame], aujourd_hui: pd.Timestamp, retard_max_jours: int = 4,
              ecart_max_jours: int = 3) -> tuple[pd.Timestamp, set[str], bool]:
    """Contrôle la fraîcheur des cours.

    Renvoie la dernière séance disponible, les actifs dont la dernière bougie est trop ancienne par rapport
    à cette séance (exclus du scan) et True si la séance elle-même est trop ancienne (aucun signal envoyé).
    """
    seance = max(df.index[-1] for df in data.values())
    perimes = {s for s, df in data.items() if (seance - df.index[-1]).days > ecart_max_jours}
    return seance, perimes, (aujourd_hui.normalize() - seance.normalize()).days > retard_max_jours
