"""Envoi des alertes sur Telegram (si TELEGRAM_TOKEN et TELEGRAM_CHAT_ID sont définis)."""
from __future__ import annotations

import os

import httpx

from .scanner import Signal


JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]


def date_fr(d) -> str:
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]} {d.year}"


def format_signal(s: Signal, plan_txt: str = "") -> str:
    return (f"ACHAT {s.nom} ({s.symbole}) | {s.type_trading.upper()} | {s.strategie}\n"
            f"Signal à la clôture du {date_fr(s.date)}\n"
            f"Stop {s.stop:.2f} | Objectif {s.objectif:.2f} | Ratio gain/perte {s.ratio:.1f} | "
            f"Risque {s.risque_pct:.1f} % du prix\n" + plan_txt)


def format_cloture(c: dict) -> str:
    return (f"{c['statut'].upper()} {c['nom']} ({c['strategie']}, signal du {c['date_signal']}) : "
            f"sortie le {c['date_sortie']} ({c['motif']}), "
            f"{c['prix_entree']} → {c['prix_sortie']}, {float(c['r']):+.2f} R")


def message(signaux: list[Signal], clotures: list[dict], bilan: dict, seance, plans: dict | None = None) -> str:
    plans = plans or {}
    parties = [f"Signaux de la séance du {date_fr(seance)}\n(positions simulées, pas un conseil)"]
    if signaux:
        parties.append("\n\n".join(format_signal(s, plans.get(id(s), "")) for s in signaux))
        parties.append("Coûts estimés (spreads des heures principales, financement estimé). "
                       "Vérifiez la taille minimale de contrat sur IG avant de passer l'ordre.")
    if clotures:
        parties.append("Signaux clôturés :\n" + "\n".join(format_cloture(c) for c in clotures))
    taux = f"{bilan['taux_reussite']} %" if bilan["taux_reussite"] is not None else "n.d."
    parties.append(f"Bilan au {seance:%d/%m/%Y} : {bilan['succes']} succès, {bilan['echecs']} échecs (réussite {taux}, "
                   f"{bilan['r_total']:+} R), {bilan['ouverts']} ouverts, {bilan['en_attente']} en attente.")
    return "\n\n".join(parties)


def send_telegram(texte: str) -> bool:
    token, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    r = httpx.post(f"https://api.telegram.org/bot{token}/sendMessage",
                   data={"chat_id": chat, "text": texte[:4000]}, timeout=15)
    r.raise_for_status()
    return True
