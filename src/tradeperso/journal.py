"""Journal des signaux : chaque signal émis est suivi jusqu'à sa clôture (succès ou échec)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import backtest
from .scanner import Signal
from .strategies import STRATEGIES

COLONNES = ["date_signal", "symbole", "nom", "type", "strategie", "entree_prevue", "stop", "objectif", "ratio",
            "sens", "statut", "date_entree", "prix_entree", "date_sortie", "prix_sortie", "motif", "r"]
TEXTE = ["date_signal", "symbole", "nom", "type", "strategie", "statut", "date_entree", "date_sortie", "motif"]
EN_COURS = {"en attente", "ouvert"}
CLOS = ["succès", "échec", "neutre"]
SEUIL_NEUTRE = 0.05  # |R| sous ce seuil : sortie au prix d'entrée (stop remonté), ni gain ni perte


def _types(journal: pd.DataFrame) -> pd.DataFrame:
    journal = journal.reindex(columns=COLONNES)
    journal[TEXTE] = journal[TEXTE].astype(object)
    num = [c for c in COLONNES if c not in TEXTE]
    journal[num] = journal[num].astype(float)
    return journal


def charger(path: Path) -> pd.DataFrame:
    if path.exists():
        return _types(pd.read_csv(path, dtype={c: object for c in TEXTE}))
    return _types(pd.DataFrame(columns=COLONNES))


def sauver(journal: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    journal[COLONNES].to_csv(path, index=False)


def ajouter(journal: pd.DataFrame, signaux: list[Signal]) -> pd.DataFrame:
    """Ajoute les nouveaux signaux (un même actif/stratégie/date n'est jamais compté deux fois)."""
    deja = set(zip(journal["date_signal"], journal["symbole"], journal["strategie"]))
    lignes = []
    for s in signaux:
        cle = (f"{s.date:%Y-%m-%d}", s.symbole, s.strategie)
        if cle in deja:
            continue
        lignes.append({"date_signal": cle[0], "symbole": s.symbole, "nom": s.nom, "type": s.type_trading,
                       "strategie": s.strategie, "entree_prevue": round(s.entree, 4), "stop": round(s.stop, 4),
                       "objectif": round(s.objectif, 4), "ratio": round(s.ratio, 2), "sens": s.sens, "statut": "en attente"})
    if not lignes:
        return journal
    return _types(pd.concat([journal, _types(pd.DataFrame(lignes))], ignore_index=True))


def mettre_a_jour(journal: pd.DataFrame, data: dict[str, pd.DataFrame], frais_bps: float = 5.0,
                  breakeven_r: float | None = None) -> list[dict]:
    """Rejoue chaque signal en cours sur les nouvelles bougies. Renvoie les signaux clôturés pendant cette mise à jour."""
    frais = frais_bps / 10_000
    clotures = []
    for i, row in journal.iterrows():
        df = data.get(row["symbole"])
        strat = STRATEGIES.get(row["strategie"])
        d = pd.Timestamp(row["date_signal"])
        if row["statut"] not in EN_COURS or df is None or strat is None or d not in df.index:
            continue
        sens = -1 if row["sens"] == -1 else 1
        s = strat.fonction(df).loc[d:].copy()
        s["entry"] = False
        s.loc[d, ["entry", "stop", "target"]] = [True, row["stop"], row["objectif"]]
        if len(s) < 2:
            continue
        trades = backtest.run(s, row["symbole"], frais_bps, sens, breakeven_r)
        ouverture = s["Open"].iloc[1]
        if sens * (ouverture - row["stop"]) <= 0:
            journal.loc[i, ["statut", "motif"]] = ["annulé", "ouverture au-delà du stop"]
            continue
        journal.loc[i, ["statut", "date_entree", "prix_entree"]] = [
            "ouvert", f"{s.index[1]:%Y-%m-%d}", round(ouverture * (1 + sens * frais), 4)]
        if trades:
            t = trades[0]
            journal.loc[i, ["statut", "date_sortie", "prix_sortie", "motif", "r"]] = [
                statut(t.r), f"{t.sortie_date:%Y-%m-%d}", round(t.sortie, 4), t.motif,
                round(t.r, 2)]
            clotures.append(journal.loc[i].to_dict())
    return clotures


def statut(r: float) -> str:
    return "neutre" if abs(r) < SEUIL_NEUTRE else ("succès" if r > 0 else "échec")


def bilan(journal: pd.DataFrame) -> dict:
    clos = journal[journal["statut"].isin(CLOS)]
    r = pd.to_numeric(clos["r"])
    ok, ko = int((clos["statut"] == "succès").sum()), int((clos["statut"] == "échec").sum())
    return {
        "clos": len(clos),
        "succes": int((clos["statut"] == "succès").sum()),
        "echecs": int((clos["statut"] == "échec").sum()),
        "neutres": int((clos["statut"] == "neutre").sum()),
        "taux_reussite": round(100 * ok / (ok + ko), 1) if ok + ko else None,
        "r_total": round(r.sum(), 2) if len(clos) else 0.0,
        "ouverts": int((journal["statut"] == "ouvert").sum()),
        "en_attente": int((journal["statut"] == "en attente").sum()),
    }


def to_markdown(journal: pd.DataFrame) -> str:
    b = bilan(journal)
    taux = f"{b['taux_reussite']} %" if b["taux_reussite"] is not None else "n.d."
    md = [f"# Suivi des signaux (mis à jour le {pd.Timestamp.today():%d/%m/%Y})\n",
          f"**{b['clos']} signaux clôturés : {b['succes']} succès, {b['echecs']} échecs, {b['neutres']} neutres "
          f"(réussite {taux}, résultat cumulé {b['r_total']:+} R).** "
          f"{b['ouverts']} positions ouvertes, {b['en_attente']} en attente d'entrée.\n",
          "R = gain ou perte en multiple du risque pris (1 R = perte si le stop est touché). "
          "Neutre = sortie au prix d'entrée après remontée du stop.\n"]
    clos = journal[journal["statut"].isin(CLOS)]
    if len(clos):
        md.append("## Par stratégie\n\n| Type | Stratégie | Clôturés | Succès | Échecs | Réussite | Résultat |\n"
                  "| --- | --- | --- | --- | --- | --- | --- |")
        for (typ, strat), g in clos.groupby(["type", "strategie"]):
            n, ok = len(g), int((g["statut"] == "succès").sum())
            md.append(f"| {typ} | {strat} | {n} | {ok} | {n - ok} | {100 * ok / n:.0f} % | "
                      f"{pd.to_numeric(g['r']).sum():+.2f} R |")
        md.append("")
    md.append("## Journal (plus récents en premier)\n\n| Signal | Actif | Type | Stratégie | Entrée prévue | Stop | "
              "Objectif | Ratio | Statut | Sortie | Résultat |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for _, r in journal.iloc[::-1].head(50).iterrows():
        sortie = f"{r['date_sortie']} ({r['motif']})" if isinstance(r["date_sortie"], str) else "-"
        res = f"{float(r['r']):+.2f} R" if pd.notna(r["r"]) else "-"
        sens = "vente" if r["sens"] == -1 else "achat"
        md.append(f"| {r['date_signal']} | {r['nom']} | {sens} | {r['type']} | {r['strategie']} | {r['entree_prevue']} | "
                  f"{r['stop']} | {r['objectif']} | {r['ratio']} | {r['statut']} | {sortie} | {res} |")
    return "\n".join(md) + "\n"

