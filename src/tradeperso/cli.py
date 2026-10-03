"""Ligne de commande : `tradeperso scan` et `tradeperso backtest`."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from . import alerts, backtest, execution, journal
from .data import download, load_config, prochains_resultats, watchlist
from .scanner import scan, to_markdown
from .strategies import STRATEGIES, appliquer, regime_haussier

SP500 = "^GSPC"


def cmd_scan(cfg: dict, out: Path) -> None:
    noms = watchlist(cfg)
    filtres = cfg.get("filtres", {})
    breakeven_r = filtres.get("stop_a_l_entree_apres_r")
    jrn = journal.charger(out / "journal.csv")
    en_cours = set(jrn[jrn["statut"].isin(journal.EN_COURS)]["symbole"])
    data = download(sorted(set(noms) | en_cours | {SP500} | set(execution.FX_TICKERS.values())), period="2y")
    fx = execution.taux_change(data)
    data = {s: df for s, df in data.items() if s not in execution.FX_TICKERS.values()}
    clotures = journal.mettre_a_jour(jrn, data, cfg["capital"]["frais_bps"], breakeven_r)
    en_cours = set(jrn[jrn["statut"].isin(journal.EN_COURS)]["symbole"])
    regime = regime_haussier(data[SP500]) if filtres.get("filtre_marche") and SP500 in data else None
    max_pos = filtres.get("max_positions")
    signaux = scan({s: data[s] for s in noms if s in data}, noms,
                   cfg["capital"]["montant"], cfg["capital"]["risque_par_trade"], cfg["capital"].get("ratio_min", 0.0),
                   regime=regime, indices=set(cfg.get("indices", {})), exclus=en_cours)
    # Actions : pas d'achat dans les jours qui précèdent une publication de résultats.
    jours = filtres.get("jours_avant_resultats", 0)
    resultats = {s.symbole: prochains_resultats(s.symbole) for s in signaux if s.symbole not in cfg.get("indices", {})}
    seance = max(df.index[-1] for df in data.values())
    signaux = [s for s in signaux if not (jours and resultats.get(s.symbole)
                                          and (resultats[s.symbole] - seance.date()).days <= jours + 2)]
    if max_pos:
        signaux = signaux[:max(0, max_pos - len(en_cours))]
    jrn = journal.ajouter(jrn, signaux)
    journal.sauver(jrn, out / "journal.csv")
    (out / "suivi.md").write_text(journal.to_markdown(jrn), encoding="utf-8")
    plans = {id(s): execution.plan(s, cfg, fx) for s in signaux}
    for s in signaux:
        plans[id(s)].resultats = resultats.get(s.symbole)
    marche = ("" if regime is None else
              f"Marché (S&P 500 vs moyenne 200 jours) : {'haussier, achats seulement' if regime.iloc[-1] else 'baissier, ventes sur indices seulement'}.  \n")
    md = (f"# Signaux de la séance du {alerts.date_fr(seance)}\n\n"
          f"Calculés le {date.today():%d/%m/%Y} sur les cours de clôture du {seance:%d/%m/%Y}.  \n" + marche
          + f"Positions en cours : {len(en_cours)} sur {max_pos or 'illimité'}.\n\n"
          + to_markdown(signaux)
          + "".join(f"\n### {s.nom} ({s.strategie})\n\n" + execution.format_plan(s, plans[id(s)]).replace("\n", "  \n") + "\n" for s in signaux))
    (out / "signaux.md").write_text(md, encoding="utf-8")
    print(md)
    if (signaux or clotures) and alerts.send_telegram(
            alerts.messages(signaux, clotures, journal.bilan(jrn), seance, plans, breakeven_r)):
        print("Alerte Telegram envoyée.")


def cmd_backtest(cfg: dict, out: Path, period: str) -> None:
    noms = watchlist(cfg)
    data = download(list(noms), period=period)
    frais, risque = cfg["capital"]["frais_bps"], cfg["capital"]["risque_par_trade"]
    filtres = cfg.get("filtres", {})
    breakeven_r = filtres.get("stop_a_l_entree_apres_r")
    regime = regime_haussier(data[SP500]) if filtres.get("filtre_marche") and SP500 in data else None
    indices = set(cfg.get("indices", {}))
    cols = ["stratégie", "trades", "reussite_pct", "r_moyen", "profit_factor", "rendement_pct", "drawdown_max_pct"]

    def table(reg, be) -> str:
        lignes = []
        for nom_strat, st in STRATEGIES.items():
            trades = [t for sym, df in data.items() if not st.indices_seulement or sym in indices
                      for t in backtest.run(appliquer(nom_strat, df, reg), sym, frais, st.sens, be)]
            lignes.append({"stratégie": nom_strat + ("" if st.actif else " (test)"), **backtest.metrics(trades, risque)})
        return "| " + " | ".join(cols) + " |\n|" + " --- |" * len(cols) + "\n" + "".join(
            "| " + " | ".join(str(l.get(c, "")) for c in cols) + " |\n" for l in lignes)

    md = (f"# Backtest sur {period} ({len(data)} actifs, frais {frais} bps, risque {risque:.0%} par trade)\n\n"
          "Ventes à découvert : indices uniquement. Chaque trade est compté sans limite de positions simultanées.\n\n"
          f"## Avec protections\n\nFiltre de marché S&P 500 / MM200 : {'oui' if regime is not None else 'non'}. "
          f"Stop ramené au prix d'entrée à +{breakeven_r} R : {'oui' if breakeven_r else 'non'}.\n\n"
          + table(regime, breakeven_r)
          + "\n## Sans protections (pour comparaison)\n\n" + table(None, None)
          + "\n" + pareto(data, noms, indices, regime, breakeven_r, frais, cfg["capital"].get("ratio_min", 0.0))
          + "\nRésultats passés : aucune garantie pour l'avenir.\n")
    out.mkdir(parents=True, exist_ok=True)
    (out / "backtest.md").write_text(md, encoding="utf-8")
    print(md)


def pareto(data, noms, indices, regime, breakeven_r, frais, ratio_min) -> str:
    """Loi des 20/80 par actif : quelle part du gain vient des meilleurs actifs, et est-ce stable dans le temps ?"""
    trades = []
    for nom_strat, st in STRATEGIES.items():
        if not st.actif:
            continue
        for sym, df in data.items():
            if st.indices_seulement and sym not in indices:
                continue
            out = appliquer(nom_strat, df, regime)
            e = out[out["entry"]]
            if len(e) and ((e["target"] - e["Close"]).abs() / (e["Close"] - e["stop"]).abs()).median() < ratio_min - 1e-9:
                break  # stratégie jamais envoyée (ratio trop faible)
            trades += backtest.run(out, sym, frais, st.sens, breakeven_r)
    if not trades:
        return ""
    t = pd.DataFrame({"sym": [x.symbole for x in trades], "date": [x.sortie_date for x in trades], "r": [x.r for x in trades]})
    milieu = t["date"].min() + (t["date"].max() - t["date"].min()) / 2
    t["periode"] = np.where(t["date"] < milieu, "avant", "apres")
    par = t.groupby("sym")["r"].agg(["count", "sum"]).sort_values("sum", ascending=False)
    moities = t.pivot_table(index="sym", columns="periode", values="r", aggfunc="sum", fill_value=0.0)
    par = par.join(moities).fillna(0.0)
    positif = par["sum"].clip(lower=0).sum()
    par["cumul"] = 100 * par["sum"].clip(lower=0).cumsum() / positif if positif else 0.0
    n80 = int((par["cumul"] < 80).sum()) + 1
    # Test de stabilité : top 20 % choisi sur la 1re moitié, jugé sur la 2e moitié.
    top = moities.sort_values("avant", ascending=False).index[:max(1, round(0.2 * len(moities)))]
    apres = t[t["periode"] == "apres"]
    r_top = apres[apres["sym"].isin(top)]["r"].mean()
    r_autres = apres[~apres["sym"].isin(top)]["r"].mean()
    lignes = [f"## Loi des 20/80 par actif (stratégies envoyées, avec protections)\n",
              f"**{n80} actifs sur {len(par)} ({100 * n80 / len(par):.0f} %) font 80 % des gains.**\n",
              f"Stabilité : les {len(top)} meilleurs actifs de la 1re moitié ({milieu:%Y}) font {r_top:+.2f} R par trade "
              f"dans la 2e moitié, contre {r_autres:+.2f} R pour les autres.\n",
              "| Rang | Actif | Trades | Résultat | Part cumulée du gain | 1re moitié | 2e moitié |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for i, (sym, r) in enumerate(par.iterrows(), 1):
        lignes.append(f"| {i} | {noms.get(sym, sym)} | {int(r['count'])} | {r['sum']:+.1f} R | {r['cumul']:.0f} % | "
                      f"{r.get('avant', 0.0):+.1f} R | {r.get('apres', 0.0):+.1f} R |")
    return "\n".join(lignes) + "\n"


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
