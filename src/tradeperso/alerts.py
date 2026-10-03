"""Envoi des alertes sur Telegram (si TELEGRAM_TOKEN et TELEGRAM_CHAT_ID sont définis)."""
from __future__ import annotations

import os

import httpx

from .scanner import Signal


def format_signal(s: Signal) -> str:
    return (f"ACHAT {s.nom} ({s.symbole}) | {s.type_trading.upper()} | {s.strategie}\n"
            f"Entrée ≈ {s.entree:.2f} | Stop {s.stop:.2f} | Objectif {s.objectif:.2f}\n"
            f"Ratio gain/perte {s.ratio:.1f} | Risque {s.risque_pct:.1f} % | Quantité {s.quantite}")


def format_cloture(c: dict) -> str:
    return (f"{c['statut'].upper()} {c['nom']} ({c['strategie']}) : {c['motif']}, "
            f"{c['prix_entree']} → {c['prix_sortie']}, {float(c['r']):+.2f} R")


def message(signaux: list[Signal], clotures: list[dict], bilan: dict) -> str:
    parties = ["Signaux du jour (simulation, pas un conseil)"]
    if signaux:
        parties.append("\n\n".join(format_signal(s) for s in signaux))
    if clotures:
        parties.append("Signaux clôturés :\n" + "\n".join(format_cloture(c) for c in clotures))
    taux = f"{bilan['taux_reussite']} %" if bilan["taux_reussite"] is not None else "n.d."
    parties.append(f"Bilan : {bilan['succes']} succès, {bilan['echecs']} échecs (réussite {taux}, "
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
