"""Ligne de commande : `tradeperso scan` et `tradeperso backtest`."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from . import alerts, backtest, execution, journal, portefeuille, speculation
from .data import download, fraicheur, load_config, prochains_resultats, watchlist
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
    seance, perimes, en_retard = fraicheur(data, pd.Timestamp.today())
    clotures = journal.mettre_a_jour(jrn, data, cfg["capital"]["frais_bps"], breakeven_r)
    en_cours = set(jrn[jrn["statut"].isin(journal.EN_COURS)]["symbole"])
    regime = regime_haussier(data[SP500]) if filtres.get("filtre_marche") and SP500 in data else None
    max_pos = filtres.get("max_positions")
    signaux = [] if en_retard else scan({s: data[s] for s in noms if s in data and s not in perimes}, noms,
                   cfg["capital"]["montant"], cfg["capital"]["risque_par_trade"], cfg["capital"].get("ratio_min", 0.0),
                   regime=regime, indices=set(cfg.get("indices", {})), exclus=en_cours)
    # Actions : pas d'achat dans les jours qui précèdent une publication de résultats.
    jours = filtres.get("jours_avant_resultats", 0)
    resultats = {s.symbole: prochains_resultats(s.symbole) for s in signaux if s.symbole not in cfg.get("indices", {})}
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
          + (f"**⚠️ Données en retard : dernière séance du {seance:%d/%m/%Y}. Aucun nouveau signal.**\n\n" if en_retard else "")
          + (f"Cours non à jour, actifs exclus : {', '.join(sorted(noms.get(s, s) for s in perimes))}.\n\n" if perimes else "")
          + to_markdown(signaux)
          + recents(data, noms)
          + "".join(f"\n### {s.nom} ({s.strategie})\n\n" + execution.format_plan(s, plans[id(s)]).replace("\n", "  \n") + "\n" for s in signaux))
    (out / "signaux.md").write_text(md, encoding="utf-8")
    print(md)
    if (signaux or clotures) and alerts.send_telegram(
            alerts.messages(signaux, clotures, journal.bilan(jrn), seance, plans, breakeven_r)):
        print("Alerte Telegram envoyée.")
    if not en_retard and SP500 in data:
        cmd_speculation(cfg, out, data, noms, seance, regime)
    if en_retard and alerts.send_telegram([f"⚠️ <b>Données en retard</b>\nDernière séance reçue : {alerts.date_courte(seance)}.\n"
                                           "Aucun signal envoyé ce soir."]):
        print("Alerte de retard envoyée.")


def cmd_speculation(cfg, out, data, noms, seance, regime) -> None:
    """Classement des actions leaders ; la sélection est revue le vendredi (ou au premier passage)."""
    sc = cfg.get("speculation")
    if not sc:
        return
    actions = {s: data[s] for s in cfg.get("actions_us", {}) if s in data}
    t = speculation.classement(actions, noms, data[SP500], sc.get("jours", 126))
    fichier = out / "speculation.txt"
    avant = speculation.charger(fichier)
    if seance.weekday() == 4 or not fichier.exists():
        baissier = sc.get("filtre_marche") and regime is not None and not bool(regime.iloc[-1])
        apres = [] if baissier else speculation.selection(t, avant, sc.get("nombre", 5))
        speculation.sauver(fichier, apres)
    else:
        apres = avant
    achats, ventes = [s for s in apres if s not in avant], [s for s in avant if s not in apres]
    (out / "speculation.md").write_text(speculation.to_markdown(t, apres, ventes, sc["capital"], seance), encoding="utf-8")
    if achats or ventes:
        part = sc["capital"] / max(len(apres), 1)
        lignes = [f"🚀 <b>Spéculation · actions leaders</b>", f"Revue du {alerts.date_courte(seance)}, en actions réelles sur eToro", ""]
        lignes += [f"🟢 Acheter <b>{noms.get(s, s)}</b> pour {alerts.euros(part)}" for s in achats]
        lignes += [f"🔴 Vendre <b>{noms.get(s, s)}</b>" for s in ventes]
        gardes = [noms.get(s, s) for s in apres if s not in achats]
        if gardes:
            lignes += ["", "Garder : " + ", ".join(gardes)]
        lignes += ["", "<i>Leaders = plus forte hausse sur 6 mois par rapport au S&P 500. Simulation, pas un conseil.</i>"]
        if alerts.send_telegram(["\n".join(lignes)]):
            print("Alerte spéculation envoyée.")


def recents(data, noms, seuil: int = 200) -> str:
    """Suivi des actions récemment introduites en bourse (historique trop court pour la moyenne 200 jours)."""
    lignes = []
    for s in sorted(noms):
        df = data.get(s)
        if df is None or len(df) >= seuil:
            continue
        c = df["Close"]
        mm50 = c.rolling(50).mean().iloc[-1]
        haut20 = df["High"].rolling(20).max().shift(1).iloc[-1]
        etat = ("moyenne 50 jours pas encore disponible" if pd.isna(mm50) else
                f"cours {c.iloc[-1]:.2f}, moyenne 50 jours {mm50:.2f} ({'au-dessus' if c.iloc[-1] > mm50 else 'en dessous'}), "
                f"plus haut 20 jours {haut20:.2f}, plus haut depuis l'introduction {df['High'].max():.2f}")
        lignes.append(f"- {noms[s]} ({len(df)} séances) : {etat}")
    if not lignes:
        return ""
    return ("\n**Nouvelles introductions** (tendance jugée sur la moyenne 50 jours en attendant 200 séances) :\n\n"
            + "\n".join(lignes) + "\n")


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
          + section_portefeuille(cfg, data, indices, frais, risque)
          + "\n# Détail par stratégie (trades indépendants)\n\n"
          "Ventes à découvert : indices uniquement. Ici, chaque trade est compté sans limite de positions "
          "simultanées : les rendements sont donc gonflés. Seuls le gain moyen (R) et le profit factor se comparent.\n\n"
          f"## Avec protections\n\nFiltre de marché S&P 500 / MM200 : {'oui' if regime is not None else 'non'}. "
          f"Stop ramené au prix d'entrée à +{breakeven_r} R : {'oui' if breakeven_r else 'non'}.\n\n"
          + table(regime, breakeven_r)
          + "\n## Sans protections (pour comparaison)\n\n" + table(None, None)
          + "\n" + pareto(data, noms, indices, regime, breakeven_r, frais, cfg["capital"].get("ratio_min", 0.0))
          + "\nRésultats passés : aucune garantie pour l'avenir.\n")
    out.mkdir(parents=True, exist_ok=True)
    (out / "backtest.md").write_text(md, encoding="utf-8")
    print(md)


VARIANTES = [
    ("Réglage actuel", {}),
    ("Cassure sur 15 jours", {"n": 15}),
    ("Cassure sur 25 jours", {"n": 25}),
    ("Moyenne longue 150 jours", {"lent": 150}),
    ("Moyenne longue 250 jours", {"lent": 250}),
    ("Stop à 1,5 ATR", {"k_stop": 1.5}),
    ("Stop à 2,5 ATR", {"k_stop": 2.5}),
    ("Sans stop au prix d'entrée", {"breakeven": None}),
    ("Sans filtre de marché", {"filtre_marche": False}),
]


GAFAM_NVDA = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"]
REPERES = {"SPY": "S&P 500 (ETF SPY, dividendes inclus)", "QQQ": "Nasdaq 100 (ETF QQQ, dividendes inclus)"}


def section_detention(data, ref, risque) -> str:
    """Compare le système à « acheter et garder » sur la même période."""
    debut, fin = ref["debut"], ref["fin"]
    try:
        reperes = download(list(REPERES), period="max")
    except Exception:
        reperes = {}
    lignes = [("**Ce système** (4 positions, risque " + f"{risque:.0%} par trade)", ref)]
    for tic, nom in REPERES.items():
        if tic in reperes:
            lignes.append((f"Garder le {nom}", portefeuille.detention(reperes[tic]["Close"], debut, fin)))
    panier = [s for s in GAFAM_NVDA if s in data]
    if panier:
        prix = pd.DataFrame({s: data[s]["Close"] for s in panier})
        lignes.append(("Garder Apple, Microsoft, Alphabet, Amazon, Meta et Nvidia (parts égales)",
                       portefeuille.detention(prix, debut, fin)))
    md = [f"### Comparaison avec « acheter et garder » ({debut:%m/%Y} à {fin:%m/%Y})\n",
          "| Méthode | Rendement par an | Total | Pire baisse | Plus longue période sous un sommet |",
          "| --- | --- | --- | --- | --- |"]
    for nom, m in lignes:
        md.append(f"| {nom} | {m['rendement_annuel_pct']:+} % | {m['rendement_total_pct']:+} % | "
                  f"{m['drawdown_max_pct']} % | {m['drawdown_duree_mois']} mois |")
    return "\n".join(md) + "\n"


def section_speculation(cfg, data) -> str:
    sc = cfg.get("speculation")
    if not sc or SP500 not in data:
        return ""
    actions = {s: data[s] for s in cfg.get("actions_us", {}) if s in data}
    md = ["### Spéculation : rotation sur les actions leaders (actions réelles, parts égales)\n",
          "| Variante | Rendement par an | Total | Pire baisse | Plus longue période sous un sommet |",
          "| --- | --- | --- | --- | --- |"]
    for libelle, reg in [("Avec filtre de marché", regime_haussier(data[SP500])), ("Sans filtre de marché", None)]:
        courbe = speculation.rotation(actions, data[SP500], sc.get("nombre", 5), sc.get("jours", 126),
                                      cfg["capital"]["frais_bps"], reg)
        m = portefeuille.detention(courbe, courbe.index[sc.get("jours", 126)], courbe.index[-1])
        md.append(f"| {libelle} | {m['rendement_annuel_pct']:+} % | {m['rendement_total_pct']:+} % | "
                  f"{m['drawdown_max_pct']} % | {m['drawdown_duree_mois']} mois |")
    md.append("\n⚠️ Biais : la liste contient les grandes actions d'aujourd'hui, donc des gagnantes connues après coup. "
              "Le résultat réel sera plus faible.\n")
    return "\n".join(md) + "\n"


def section_portefeuille(cfg, data, indices, frais, risque) -> str:
    """Résultat réaliste (limite de positions) et solidité des réglages."""
    f = cfg.get("filtres", {})
    max_pos, ratio_min = f.get("max_positions", 4), cfg["capital"].get("ratio_min", 0.0)
    lignes = []
    for libelle, v in VARIANTES:
        v = dict(v)
        be = v.pop("breakeven", f.get("stop_a_l_entree_apres_r"))
        fm = v.pop("filtre_marche", f.get("filtre_marche", False))
        cands = portefeuille.candidats(data, indices, frais, ratio_min, fm, be, SP500, **v)
        lignes.append((libelle, portefeuille.simuler(cands, max_positions=max_pos, risque=risque)))
    ref = lignes[0][1]
    if not ref.get("trades"):
        return "## Portefeuille\n\nAucun trade.\n"
    comparaison = section_detention(data, ref, risque)
    md = [f"## Résultat réaliste du portefeuille (stratégies actives, {max_pos} positions au maximum)\n",
          f"**{ref['rendement_annuel_pct']:+} % par an** ({ref['rendement_total_pct']:+} % au total), "
          f"pire baisse **{ref['drawdown_max_pct']} %**, plus longue période sous un ancien sommet : "
          f"{ref['drawdown_duree_mois']} mois.\n",
          "| Trades | Réussite | Gain moyen | Perte moyenne | Espérance par trade | Profit factor |",
          "| --- | --- | --- | --- | --- | --- |",
          f"| {ref['trades']} | {ref['reussite_pct']} % | {ref['gain_moyen_r']:+} R | {ref['perte_moyenne_r']:+} R | "
          f"{ref['esperance_r']:+} R | {ref['profit_factor']} |\n",
          "Par stratégie : " + ", ".join(f"{s} {n} trades ({r:+} R)" for s, (n, r) in ref["par_strategie"].items()) + ".\n",
          comparaison,
          section_speculation(cfg, data),
          "## Solidité des réglages\n",
          "Si un petit changement de réglage fait s'effondrer le résultat, la stratégie est trop ajustée au passé.\n",
          "| Variante | Trades | Espérance par trade | Rendement par an | Pire baisse |",
          "| --- | --- | --- | --- | --- |"]
    for libelle, m in lignes:
        if m.get("trades"):
            md.append(f"| {libelle} | {m['trades']} | {m['esperance_r']:+} R | {m['rendement_annuel_pct']:+} % | "
                      f"{m['drawdown_max_pct']} % |")
    return "\n".join(md) + "\n"


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
