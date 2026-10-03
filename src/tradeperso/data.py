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
