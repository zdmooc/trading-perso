"""Test honnête de 6 pistes pour améliorer les signaux. Usage : python scripts/signaux.py

Principe : chaque réglage est choisi sur la période « apprentissage » (avant 2026 pour le plan du jour, avant 2023
pour le swing), puis vérifié sur la période « contrôle », jamais utilisée pour choisir. Une piste n'est retenue que
si elle aide sur la période de contrôle.

Plan du jour (bougies horaires Yahoo, points nets du spread IG) :
1. Règle choisie sur l'apprentissage seulement, comparée à la règle actuelle (choisie sur toute la période).
2. Jours à éviter : annonces américaines (emploi le 1er vendredi du mois, Fed) et veille trop étroite ou trop large.
3. Sorties : objectif 2R ou 4R au lieu de 3R, moitié encaissée à 1,5R, ou aucune cible (sortie à la clôture).
4. Les 3 indices ensemble : un seul trade Nasdaq / S&P quand les deux partent dans le même sens, arrêt après 2 pertes.
5. Vente DAX quand le RSI 4 h est haut (piste déjà repérée), coupée en deux périodes.
Swing (bougies journalières, 10 ans) :
5. Classement des signaux quand les 4 places sont prises, sortie au bout de N jours.
6. Coûts réels : non calculables ici (pas d'historique d'ordres eToro) ; voir le rapport.
"""
from __future__ import annotations

import gzip
import pickle
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from tradeperso import backtest, matin, plan, portefeuille
from tradeperso.data import download, load_config, watchlist

import ameliorations  # noqa: E402  (même dossier)

COUPURE = pd.Timestamp("2026-01-01").date()
COUPURE_SWING = pd.Timestamp("2023-01-01")
DONNEES = Path("reports/tmp/donnees.pkl.gz")

# Annonces de la Fed (le soir, pendant la séance américaine).
FED = {pd.Timestamp(x).date() for x in [
    "2023-12-13", "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07",
    "2024-12-18", "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29",
    "2025-12-10", "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28"]}


def annonce(jour) -> bool:
    """Jour de la Fed ou 1er vendredi du mois (chiffres de l'emploi américain)."""
    j = pd.Timestamp(jour)
    return jour in FED or (j.dayofweek == 4 and j.day <= 7)


def rejouer(barres, liste, fin_entree, spread, us, ratio: float | None = 3.0, partiel: float | None = None):
    """Comme plan.rejouer, avec un objectif réglable (None : sortie à la clôture) et une moitié encaissée à
    `partiel` R (stop ramené à l'entrée ensuite). Renvoie (points, sens, heure d'entrée, heure de sortie) ou None."""
    pos = None
    for b in barres.itertuples():
        if pos is None:
            if plan.heure_normale(b.Index, us) > fin_entree:
                continue
            touches = [o for o in liste if (b.High >= o.niveau if o.cote == "haut" else b.Low <= o.niveau)]
            if not touches:
                continue
            o = min(touches, key=lambda o: abs(b.Open - o.niveau))
            e = max(b.Open, o.niveau) if o.cote == "haut" else min(b.Open, o.niveau)
            s = o.sens
            pos = dict(s=s, e=e, r=o.risque, stop=e - s * o.risque, obj=e + s * ratio * o.risque if ratio else None,
                       demi=None, t0=b.Index)
            if (b.Close <= pos["stop"]) if s > 0 else (b.Close >= pos["stop"]):
                return -o.risque - spread, s, b.Index, b.Index
            continue
        s, e = pos["s"], pos["e"]
        if (b.Low <= pos["stop"]) if s > 0 else (b.High >= pos["stop"]):
            fin = s * (pos["stop"] - e)
            return (fin if pos["demi"] is None else (pos["demi"] + fin) / 2) - spread, s, pos["t0"], b.Index
        if pos["obj"] is not None and ((b.High >= pos["obj"]) if s > 0 else (b.Low <= pos["obj"])):
            fin = s * (pos["obj"] - e)
            return (fin if pos["demi"] is None else (pos["demi"] + fin) / 2) - spread, s, pos["t0"], b.Index
        if partiel and pos["demi"] is None and ((b.High >= e + partiel * pos["r"]) if s > 0 else (b.Low <= e - partiel * pos["r"])):
            pos["demi"], pos["stop"] = partiel * pos["r"], e
    if pos is None:
        return None
    fin = pos["s"] * (float(barres["Close"].iloc[-1]) - pos["e"])
    return (fin if pos["demi"] is None else (pos["demi"] + fin) / 2) - spread, pos["s"], pos["t0"], barres.index[-1]


SORTIES = {"3R (actuel)": dict(ratio=3.0), "2R": dict(ratio=2.0), "4R": dict(ratio=4.0),
           "moitié à 1,5R puis 3R": dict(ratio=3.0, partiel=1.5), "sans objectif, sortie à la clôture": dict(ratio=None)}


def journees(h, d, info):
    """(veille, jour, séance du jour, plus haut, plus bas, ATR, tendance) de chaque jour testable."""
    us = info.get("us", False)
    ses, ctx = plan.seances(h, info["heures"], info.get("debut_min", 0), us), plan.contexte(d)
    jours = sorted(ses)
    for veille, jour in zip(jours, jours[1:]):
        if veille in ctx.index:
            g, c = ses[veille], ctx.loc[veille]
            yield jour, ses[jour], float(g["High"].max()), float(g["Low"].min()), float(c["atr"]), int(c["tendance"])


def trades_indice(h, d, info) -> pd.DataFrame:
    """Un trade par jour, règle et sortie."""
    lignes = []
    for jour, barres, hi, lo, a, tend in journees(h, d, info):
        for r in plan.REGLES:
            liste = plan.ordres(r, hi, lo, a, tend)
            for nom, opt in SORTIES.items():
                t = rejouer(barres, list(liste), info["fin_entree"], info["spread"], info.get("us", False), **opt)
                if t is not None:
                    lignes.append(dict(jour=jour, regle=r.cle, sortie=nom, pts=t[0], sens=t[1], t0=t[2], t1=t[3],
                                       largeur=(hi - lo) / a, annonce=annonce(jour)))
    return pd.DataFrame(lignes)


def resume(p: pd.Series, taille: float) -> str:
    if not len(p):
        return "0 trade"
    g = (p > 0).mean()
    return f"{len(p)} trades · {round(100 * g)} % gagnés · {plan.pts(p.sum())} = {plan.eur(p.sum() * taille)}"


def cellule(p: pd.Series, taille: float) -> str:
    return f"{plan.pts(p.sum())} = {plan.eur(p.sum() * taille)} ({len(p)} tr., {round(100 * (p > 0).mean()) if len(p) else 0} %)"


def par_mois(p: pd.Series, mois: float, taille: float) -> str:
    return plan.eur(p.sum() * taille / mois)


def section_jour(T: dict, actuelles: dict) -> tuple[list[str], dict]:
    md, choix = ["# Plan du jour : règle choisie avant 2026, vérifiée sur 2026", ""], {}
    for s, info in plan.INDICES.items():
        if s not in T:
            continue
        t = T[s][T[s]["sortie"] == "3R (actuel)"]
        app, ctl = t[t["jour"] < COUPURE], t[t["jour"] >= COUPURE]
        tot = app.groupby("regle")["pts"].agg(["sum", "count"])
        tot = tot[tot["count"] >= plan.MIN_TRADES]
        choix[s] = tot["sum"].idxmax()
        md += [f"## {info['nom']}", "",
               f"Apprentissage du {app['jour'].min():%d/%m/%Y} au 31/12/2025, contrôle du 01/01/2026 au {ctl['jour'].max():%d/%m/%Y}.", "",
               "| Règle | Apprentissage | Contrôle 2026 |", "| --- | --- | --- |"]
        ordre = tot.sort_values("sum", ascending=False).index
        for k in ordre:
            marque = (" ← choisie avant 2026" if k == choix[s] else "") + (" ← règle actuelle" if k == actuelles.get(s) else "")
            md.append(f"| {plan.PAR_CLE[k].nom}{marque} | {cellule(app[app['regle'] == k]['pts'], info['taille'])} | "
                      f"{cellule(ctl[ctl['regle'] == k]['pts'], info['taille'])} |")
        rang = ctl.groupby("regle")["pts"].sum().rank(ascending=False)
        md += ["", f"La règle choisie avant 2026 finit **{int(rang.get(choix[s], 0))}e sur {len(rang)}** en 2026.", ""]
    return md, choix


def filtres(t: pd.DataFrame) -> dict[str, pd.Series]:
    return {"Sans filtre": t["pts"] * 0 == 0,
            "Sans les jours d'annonce": ~t["annonce"],
            "Sans veille étroite (< 0,5 ATR)": t["largeur"] >= 0.5,
            "Sans veille large (> 1,5 ATR)": t["largeur"] <= 1.5,
            "Les trois": ~t["annonce"] & t["largeur"].between(0.5, 1.5)}


def section_variantes(T: dict, choix: dict) -> list[str]:
    md = ["# Jours à éviter et sorties", "",
          "Pour chaque indice, avec la règle choisie avant 2026. Une colonne par période.", ""]
    for s, info in plan.INDICES.items():
        if s not in T:
            continue
        t = T[s][T[s]["regle"] == choix[s]]
        app, ctl = (lambda x: x[x["jour"] < COUPURE]), (lambda x: x[x["jour"] >= COUPURE])
        base = t[t["sortie"] == "3R (actuel)"]
        md += [f"## {info['nom']} : {plan.PAR_CLE[choix[s]].nom}", "", "| Variante | Avant 2026 | 2026 |", "| --- | --- | --- |"]
        for nom, m in filtres(base).items():
            x = base[m]
            md.append(f"| {nom} | {cellule(app(x)['pts'], info['taille'])} | {cellule(ctl(x)['pts'], info['taille'])} |")
        for nom in SORTIES:
            if nom == "3R (actuel)":
                continue
            x = t[t["sortie"] == nom]
            md.append(f"| Sortie {nom} | {cellule(app(x)['pts'], info['taille'])} | {cellule(ctl(x)['pts'], info['taille'])} |")
        md.append("")
    return md


def ensemble(T: dict, choix: dict, correlation: bool, pertes_max: int | None) -> pd.DataFrame:
    """Les 3 indices tradés ensemble, trades en euros, dans l'ordre des heures d'entrée."""
    lignes = []
    for s, info in plan.INDICES.items():
        if s in T:
            t = T[s][(T[s]["regle"] == choix[s]) & (T[s]["sortie"] == "3R (actuel)")]
            lignes.append(t.assign(sym=s, eur=t["pts"] * info["taille"]))
    t = pd.concat(lignes).sort_values(["jour", "t0", "sym"])
    garde = []
    for _, j in t.groupby("jour"):
        pris = []
        for i, r in j.iterrows():
            if correlation and r["sym"] in ("^NDX", "^GSPC") and any(
                    t.loc[p, "sym"] in ("^NDX", "^GSPC") and t.loc[p, "sens"] == r["sens"] for p in pris):
                continue
            if pertes_max and sum(t.loc[p, "eur"] < 0 and t.loc[p, "t1"] < r["t0"] for p in pris) >= pertes_max:
                continue
            pris.append(i)
        garde += pris
    return t.loc[garde]


def section_ensemble(T: dict, choix: dict) -> list[str]:
    md = ["# Les 3 indices ensemble (en euros, tailles du plan)", "",
          "| Variante | Avant 2026 | 2026 | Pire série de pertes (2026) |", "| --- | --- | --- | --- |"]
    for nom, c, p in [("Tout prendre", False, None), ("Un seul Nasdaq / S&P dans le même sens", True, None),
                      ("Arrêt après 2 pertes dans la journée", False, 2), ("Les deux", True, 2)]:
        e = ensemble(T, choix, c, p)
        cel = []
        for x in (e[e["jour"] < COUPURE], e[e["jour"] >= COUPURE]):
            cel.append(f"{plan.eur(x['eur'].sum())} ({len(x)} tr.)")
        x = e[e["jour"] >= COUPURE]["eur"].cumsum()
        md.append(f"| {nom} | {cel[0]} | {cel[1]} | {plan.eur((x - x.cummax()).min() if len(x) else 0)} |")
    return md + [""]


def section_rsi_dax(h, d) -> list[str]:
    md = ["# Vente DAX quand le RSI 4 h est haut", "", "| Seuil | Avant 2026 | 2026 |", "| --- | --- | --- |"]
    info = plan.INDICES["^GDAXI"]
    for seuil in (30, 35):
        for nom, hh in (("avant", h[h.index.date < COUPURE]), ("2026", h[h.index.date >= COUPURE])):
            p = pd.Series(ameliorations.rebond(hh, d, info, seuil, -1), dtype=float)
            if nom == "avant":
                a = cellule(p, info["taille"])
            else:
                md.append(f"| RSI 4 h ≥ {100 - seuil} | {a} | {cellule(p, info['taille'])} |")
    return md + [""]


# ---------- swing ----------

def temps_max(cands, data, jours: int):
    """Sortie forcée à la clôture du `jours`-ième jour de bourse si le trade est encore ouvert."""
    out = []
    for c in cands:
        t, df = c.trade, data[c.trade.symbole]
        i0 = df.index.get_indexer([t.entree_date])[0]
        if i0 >= 0 and i0 + jours < len(df) and df.index[i0 + jours] < t.sortie_date:
            frais = 1 - t.sens * 5 / 10_000
            t = replace(t, sortie_date=df.index[i0 + jours], sortie=float(df["Close"].iloc[i0 + jours]) * frais, motif="temps")
        out.append(portefeuille.Candidat(c.strategie, t))
    return out


def simuler_classe(cands, cle, max_positions, risque):
    """portefeuille.simuler, mais les signaux d'un même jour passent dans l'ordre de `cle` (petit d'abord)."""
    ordre = sorted(cands, key=lambda c: (c.trade.entree_date, cle(c)))
    capital, ouverts, pris, courbe = 1.0, [], [], []
    for c in ordre:
        for pos in sorted([p for p in ouverts if p[0].trade.sortie_date < c.trade.entree_date], key=lambda p: p[0].trade.sortie_date):
            capital += pos[1] * pos[0].trade.r
            courbe.append((pos[0].trade.sortie_date, capital))
            ouverts.remove(pos)
        if len(ouverts) >= max_positions or any(p[0].trade.symbole == c.trade.symbole for p in ouverts):
            continue
        ouverts.append((c, capital * risque))
        pris.append(c)
    for pos in sorted(ouverts, key=lambda p: p[0].trade.sortie_date):
        capital += pos[1] * pos[0].trade.r
        courbe.append((pos[0].trade.sortie_date, capital))
    return portefeuille.mesures(pris, courbe)


def section_swing(cfg, data) -> list[str]:
    f, cap = cfg.get("filtres", {}), cfg["capital"]
    indices = set(cfg.get("indices", {}))
    cands = portefeuille.candidats(data, indices, cap["frais_bps"], cap.get("ratio_min", 0.0), f.get("filtre_marche", False),
                                   f.get("stop_a_l_entree_apres_r"), "^GSPC")
    mom = {s: df["Close"].pct_change(126).shift(1) for s, df in data.items()}

    def force(c):
        v = mom[c.trade.symbole].get(c.trade.entree_date, np.nan)
        return -v if np.isfinite(v) else 0.0

    classements = {"Ordre alphabétique (actuel)": lambda c: c.trade.symbole,
                   "Stop le plus serré d'abord": lambda c: abs(c.trade.entree - c.trade.stop) / c.trade.entree,
                   "Plus forte hausse sur 6 mois d'abord": force,
                   "Indices d'abord": lambda c: (c.trade.symbole not in indices, c.trade.symbole)}
    periodes = {"Avant 2023": lambda x: [c for c in x if c.trade.entree_date < COUPURE_SWING],
                "2023 à aujourd'hui": lambda x: [c for c in x if c.trade.entree_date >= COUPURE_SWING]}
    euros = cap["montant"] * cap["risque_par_trade"]
    md = ["# Swing : classement des signaux et sortie au temps", "",
          f"Scanner actuel, {f.get('max_positions', 4)} positions au maximum, {euros:.0f} € de risque par trade "
          "(R = 1 fois le risque). Rendement en % du capital swing.", "",
          "| Variante | Avant 2023 | 2023 à aujourd'hui |", "| --- | --- | --- |"]

    def ligne(nom, cs, cle):
        cel = []
        for sel in periodes.values():
            m = simuler_classe(sel(cs), cle, f.get("max_positions", 4), cap["risque_par_trade"])
            cel.append(f"{m['trades']} tr. · {m['esperance_r']:+} R par trade · {m['rendement_annuel_pct']:+} %/an · "
                       f"pire baisse {m['drawdown_max_pct']} %" if m.get("trades") else "0 trade")
        md.append(f"| {nom} | {cel[0]} | {cel[1]} |")

    for nom, cle in classements.items():
        ligne(nom, cands, cle)
    for n in (10, 20, 40, 60):
        ligne(f"Sortie au bout de {n} jours", temps_max(cands, data, n), classements["Ordre alphabétique (actuel)"])
    return md + [""]


def main() -> None:
    if DONNEES.exists():
        with gzip.open(DONNEES, "rb") as fh:
            x = pickle.load(fh)
        h, d, j = x["h"], x["d"], x["j"]
    else:
        h = matin.telecharger(plan.INDICES, "730d", "1h")
        d = matin.telecharger(plan.INDICES, "5y", "1d")
        j = download(sorted(set(watchlist(load_config())) | {"^GSPC"}), period="10y")
    cfg = load_config()
    actuelles = {}
    st = Path("reports/plan/stats.json")
    if st.exists():
        import json
        actuelles = {k: v["choisie"] for k, v in json.loads(st.read_text(encoding="utf-8"))["indices"].items()}
    T = {s: trades_indice(h[s], d[s], info) for s, info in plan.INDICES.items() if s in h and s in d}
    md1, choix = section_jour(T, actuelles)
    md = (["# Pistes pour améliorer les signaux", "",
           "Réglage choisi sur une période, vérifié sur une autre jamais utilisée pour choisir. Points nets du spread IG.", ""]
          + md1 + section_variantes(T, choix) + section_ensemble(T, choix) + section_rsi_dax(h["^GDAXI"], d["^GDAXI"])
          + section_swing(cfg, j)
          + ["Résultats passés : aucune garantie pour l'avenir.", ""])
    texte = "\n".join(md)
    Path("reports/signaux.md").write_text(texte, encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main()
