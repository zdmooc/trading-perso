"""Envoi des alertes sur Telegram (si TELEGRAM_TOKEN et TELEGRAM_CHAT_ID sont définis)."""
from __future__ import annotations

import os

import httpx

from .scanner import Signal


def format_signal(s: Signal) -> str:
    obj = f"{s.objectif:.2f}" if s.objectif else "sortie sur signal"
    return (f"ACHAT {s.nom} ({s.symbole}) [{s.strategie}]\n"
            f"Entrée ≈ {s.entree:.2f} | Stop {s.stop:.2f} | Objectif {obj}\n"
            f"Risque {s.risque_pct:.1f} % | Quantité {s.quantite}")


def send_telegram(signaux: list[Signal]) -> bool:
    token, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat or not signaux:
        return False
    texte = "Signaux du jour (simulation, pas un conseil)\n\n" + "\n\n".join(format_signal(s) for s in signaux)
    r = httpx.post(f"https://api.telegram.org/bot{token}/sendMessage",
                   data={"chat_id": chat, "text": texte[:4000]}, timeout=15)
    r.raise_for_status()
    return True
