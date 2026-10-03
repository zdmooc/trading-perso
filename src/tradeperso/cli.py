"""Ligne de commande : `tradeperso scan` et `tradeperso backtest`."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from . import alerts, backtest
from .data import download, load_config, watchlist
from .scanner import scan, to_markdown
from .strategies import STRATEGIES


def cmd_scan(cfg: dict, out: Path) -> None:
    noms = watchlist(cfg)
    data = download(list(noms), period="2y")
    signaux = scan(data, noms, cfg["capital"]["montant"], cfg["capital"]["risque_par_trade"])
    md = f"# Signaux du {date.today():%d/%m/%Y}\n\n" + to_markdown(signaux)
    out.mkdir(parents=True, exist_ok=True)
    (out / "signaux.md").write_text(md, encoding="utf-8")
    print(md)
    if alerts.send_telegram(signaux):
        print("Alerte Telegram envoyée.")


def cmd_backtest(cfg: dict, out: Path, period: str) -> None:
    noms = watchlist(cfg)
    data = download(list(noms), period=period)
    frais, risque = cfg["capital"]["frais_bps"], cfg["capital"]["risque_par_trade"]
    lignes = []
    for nom_strat, strat in STRATEGIES.items():
        trades = [t for sym, df in data.items() for t in backtest.run(strat(df), sym, frais)]
        lignes.append({"stratégie": nom_strat, **backtest.metrics(trades, risque)})
    cols = ["stratégie", "trades", "reussite_pct", "r_moyen", "profit_factor", "rendement_pct", "drawdown_max_pct"]
    table = "| " + " | ".join(cols) + " |\n|" + " --- |" * len(cols) + "\n" + "".join(
        "| " + " | ".join(str(l.get(c, "")) for c in cols) + " |\n" for l in lignes)
    md = (f"# Backtest sur {period} ({len(data)} actifs, frais {frais} bps, risque {risque:.0%} par trade)\n\n"
          + table + "\nRésultats passés : aucune garantie pour l'avenir.\n")
    out.mkdir(parents=True, exist_ok=True)
    (out / "backtest.md").write_text(md, encoding="utf-8")
    print(md)


def main() -> None:
    p = argparse.ArgumentParser(prog="tradeperso")
    p.add_argument("commande", choices=["scan", "backtest"])
    p.add_argument("--config", default="config.toml")
    p.add_argument("--out", default="reports")
    p.add_argument("--period", default="10y", help="historique du backtest (ex. 5y, 10y, max)")
    a = p.parse_args()
    cfg = load_config(a.config)
    if a.commande == "scan":
        cmd_scan(cfg, Path(a.out))
    else:
        cmd_backtest(cfg, Path(a.out), a.period)


if __name__ == "__main__":
    main()
