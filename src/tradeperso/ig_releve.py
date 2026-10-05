"""Relevé IG en lecture seule (indices, matières premières, cryptos). Aucun ordre n'est jamais passé."""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import pandas as pd

from . import alerts, matin

PANIER = {
    "Indices": ["Germany 40", "France 40", "EU Stocks 50", "FTSE 100", "US 500", "US Tech 100", "Wall Street",
                "Japan 225"],
    "Matières premières": ["Spot Gold", "Spot Silver", "Oil - Brent Crude", "Oil - US Crude", "Natural Gas",
                           "High Grade Copper"],
    "Cryptos": ["Bitcoin", "Ether", "Solana", "Ripple"],
}
COLONNES = ["horodatage", "categorie", "nom", "epic", "vente", "achat", "spread", "var_pct", "plus_haut", "plus_bas",
            "statut"]


def _choisir(marches: list[dict]) -> dict | None:
    """Produit au comptant (sans échéance), le plus petit contrat (1 €) de préférence."""
    comptant = [m for m in marches if m.get("expiry") in ("-", None, "DFB")]
    if not comptant:
        return None
    for m in comptant:
        if "(1€)" in (m.get("instrumentName") or ""):
            return m
    return comptant[0]


def _epics(ig, cache: Path) -> dict[str, str]:
    """Codes IG mémorisés dans le dépôt : on ne recherche que ceux qui manquent."""
    connus = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    for termes in PANIER.values():
        for terme in termes:
            if terme not in connus:
                m = _choisir(ig.chercher(terme))
                time.sleep(1)
                if m:
                    connus[terme] = m["epic"]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(connus, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return connus


def releve(out: Path, telegram: bool = True) -> None:
    from .ig import IG
    ig = IG()
    ig.connexion()
    dossier = out / "ig"
    epics = _epics(ig, dossier / "epics.json")
    maintenant = pd.Timestamp.now(tz=matin.PARIS)
    lignes = ["# Marchés sur IG (démo, lecture seule)", "", f"Relevé du {maintenant:%d/%m/%Y à %Hh%M} (Paris).", ""]
    fiches, rangs, resume = [], [], []
    for categorie, termes in PANIER.items():
        lignes += [f"## {categorie}", "", "| Marché | Produit | Vente | Achat | Spread | Var. jour | Plus haut | Plus bas | Statut |",
                   "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        resume.append(f"\n<b>{categorie}</b>")
        for terme in termes:
            epic = epics.get(terme)
            if not epic:
                lignes.append(f"| {terme} | introuvable | | | | | | | |")
                continue
            try:
                d = ig.marche(epic)
            except RuntimeError as e:
                lignes.append(f"| {terme} | erreur {str(e)[:60]} | | | | | | | |")
                continue
            time.sleep(1)
            sn, ins, rg = d.get("snapshot", {}), d.get("instrument", {}), d.get("dealingRules", {})
            vente, achat, var = sn.get("bid"), sn.get("offer"), sn.get("percentageChange")
            spread = round(achat - vente, 4) if achat and vente else None
            lignes.append(f"| {terme} | {ins.get('name')} | {vente} | {achat} | {spread} | {var} % | "
                          f"{sn.get('high')} | {sn.get('low')} | {sn.get('marketStatus')} |")
            rangs.append([f"{maintenant:%Y-%m-%d %H:%M}", categorie, terme, epic, vente, achat, spread, var,
                          sn.get("high"), sn.get("low"), sn.get("marketStatus")])
            devise = (ins.get("currencies") or [{}])[0].get("code", "")
            fiches.append(f"- **{terme}** `{epic}` : 1 point = {ins.get('valueOfOnePip')} {devise}, "
                          f"taille min {(rg.get('minDealSize') or {}).get('value')}, "
                          f"stop min {(rg.get('minNormalStopOrLimitDistance') or {}).get('value')}, "
                          f"marge {ins.get('marginFactor')} %")
            if var is not None:
                resume.append(f"{'🟢' if var >= 0 else '🔴'} {terme} {var:+.1f} %")
        lignes.append("")
    lignes += ["## Fiches produits", "", *fiches]
    texte = "\n".join(lignes) + "\n"
    (out / "ig_marches.md").write_text(texte, encoding="utf-8")
    # Historique : un fichier CSV par mois, une ligne par marché et par relevé.
    histo = dossier / f"cours_{maintenant:%Y-%m}.csv"
    neuf = not histo.exists()
    with histo.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if neuf:
            w.writerow(COLONNES)
        w.writerows(rangs)
    print(texte)
    if telegram:
        alerts.send_telegram(["📡 <b>Marchés IG</b>" + "\n".join(resume)])
