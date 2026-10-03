"""Plan d'exécution d'un signal sur IG et eToro : heure d'entrée, instrument, quantité et coûts estimés."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pandas as pd

from .scanner import Signal

PARIS = ZoneInfo("Europe/Paris")
FX_TICKERS = {"USD": "EURUSD=X", "GBP": "EURGBP=X", "JPY": "EURJPY=X"}
FX_DEFAUT = {"EUR": 1.0, "USD": 1.10, "GBP": 0.85, "JPY": 160.0}  # utilisés si le cours n'est pas disponible


@dataclass
class Ordre:
    plateforme: str
    instrument: str
    sous_jacent: str
    quantite: float
    unite: str
    devise: str
    perte_au_stop_eur: float
    frais_eur: float          # spread + commissions, aller-retour
    nuit_eur: float           # financement estimé par nuit (0 pour une action réelle)


@dataclass
class Plan:
    entree_paris: datetime
    bourse: str
    ordres: list[Ordre]


def taux_change(data: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Nombre d'unités de devise pour 1 EUR."""
    fx = dict(FX_DEFAUT)
    for dev, tic in FX_TICKERS.items():
        if tic in data and len(data[tic]):
            fx[dev] = float(data[tic]["Close"].iloc[-1])
    return fx


def prochaine_ouverture(date_signal: pd.Timestamp, bourse: dict) -> datetime:
    """Ouverture de la séance suivant la clôture du signal (jours fériés non gérés), en heure de Paris."""
    jour = (date_signal + pd.offsets.BDay(1)).date()
    hh, mm = map(int, bourse["ouverture"].split(":"))
    return datetime.combine(jour, time(hh, mm), ZoneInfo(bourse["tz"])).astimezone(PARIS)


def _arrondi(x: float, pas: float) -> float:
    return max(0.0, (x // pas) * pas)


def plan(s: Signal, cfg: dict, fx: dict[str, float]) -> Plan:
    ex = cfg["execution"]
    risque_eur = cfg["capital"]["montant"] * cfg["capital"]["risque_par_trade"]
    inst = cfg.get("instruments", {}).get(s.symbole)
    bourse = cfg["bourses"][inst["bourse"] if inst else "new_york"]
    ecart = s.entree - s.stop
    ordres = []

    if inst:  # indice : CFD sur IG et sur eToro
        dev, vp = inst["devise"], inst["ig_valeur_point"]
        q = round(_arrondi(risque_eur * fx[dev] / (ecart * vp), 0.01), 2)
        ordres.append(Ordre(
            "IG", f"{inst['ig']}, {vp:g} {dev} par point", "CFD sur indice", q, "contrat", dev,
            q * vp * ecart / fx[dev], q * vp * inst["ig_spread_points"] / fx[dev],
            q * vp * s.entree * ex["ig_financement_annuel"] / 365 / fx[dev]))
        dev_e = inst.get("etoro_devise", dev)
        q = round(_arrondi(risque_eur * fx[dev_e] / ecart, 0.01), 2)
        ordres.append(Ordre(
            "eToro", inst["etoro"], "CFD sur indice", q, "unité", dev_e,
            q * ecart / fx[dev_e], 2 * q * s.entree * inst["etoro_spread_pct"] / 100 / fx[dev_e],
            q * s.entree * ex["etoro_financement_annuel"] / 365 / fx[dev_e]))
    else:  # action US : CFD sur IG, action réelle sur eToro
        usd = fx["USD"]
        q = float(_arrondi(risque_eur * usd / ecart, 1))
        commission = 2 * max(q * ex["ig_action_commission_par_action"], ex["ig_action_commission_min"]) if q else 0
        ordres.append(Ordre(
            "IG", s.nom, "CFD sur action", q, "action", "USD",
            q * ecart / usd, (commission + q * s.entree * ex["ig_action_spread_pct"] / 100) / usd,
            q * s.entree * ex["ig_financement_annuel"] / 365 / usd))
        # Sans levier, la position ne peut pas dépasser le capital.
        q = round(_arrondi(min(risque_eur / ecart, cfg["capital"]["montant"] / s.entree) * usd, 0.01), 2)
        ordres.append(Ordre(
            "eToro", s.symbole, "action réelle sans levier", q, "action", "USD",
            q * ecart / usd, 2 * ex["etoro_action_commission"] / usd, 0.0))
    return Plan(prochaine_ouverture(s.date, bourse), bourse["nom"], ordres)


JOURS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]


def format_plan(s: Signal, p: Plan) -> str:
    lignes = [f"Entrée : {JOURS[p.entree_paris.weekday()]} {p.entree_paris:%d/%m/%Y à %H:%M} (heure de Paris), "
              f"à l'ouverture de la {p.bourse}, au prix du marché (≈ {s.entree:.2f})."]
    for o in p.ordres:
        if o.quantite <= 0:
            lignes.append(f"{o.plateforme} : quantité trop faible pour respecter le risque de 1 %, signal à ignorer.")
            continue
        nuit = f", financement ≈ {o.nuit_eur:.2f} €/nuit" if o.nuit_eur else ", pas de frais de nuit"
        lignes.append(f"{o.plateforme} : ACHETER {o.quantite:g} {o.unite}{'s' if o.quantite > 1 else ''} "
                      f"{o.instrument} [{o.sous_jacent}] | perte au stop ≈ {o.perte_au_stop_eur:.0f} € | "
                      f"spread + commissions ≈ {o.frais_eur:.2f} €{nuit}")
    return "\n".join(lignes)
