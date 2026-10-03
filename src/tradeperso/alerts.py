"""Alertes Telegram lisibles : un message par signal, puis un message de bilan."""
from __future__ import annotations

import html
import os

import httpx

from .execution import Plan
from .scanner import Signal

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
JOURS_COURTS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]
MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
NOMS_STRATEGIES = {
    "tendance_mm": "Suivi de tendance (moyennes mobiles 20/50)",
    "rsi2_repli": "Achat sur repli (RSI 2)",
    "cassure_20j": "Cassure du plus haut 20 jours",
}
UNITES = {"contrat": ("contrat", "contrats"), "unité": ("unité", "unités"), "action": ("action", "actions")}


def date_fr(d) -> str:
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]} {d.year}"


def date_courte(d) -> str:
    return f"{JOURS_COURTS[d.weekday()]} {d.day} {MOIS_COURTS[d.month - 1]}"


def nombre(x: float, dec: int | None = None) -> str:
    """Format français : espace pour les milliers, virgule décimale."""
    if dec is None:
        dec = 0 if abs(x) >= 1000 else 2
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def euros(x: float) -> str:
    return f"{nombre(x, 0 if x >= 10 else 2)} €"


def _ordre(o) -> str:
    if o.quantite <= 0:
        return f"<b>Sur {o.plateforme}</b>\nQuantité trop faible pour un risque de 1 % : à ignorer."
    unite = UNITES[o.unite][o.quantite > 1]
    qte = nombre(o.quantite, 0 if float(o.quantite).is_integer() else 2)
    frais = euros(o.frais_eur) + (f" + {euros(o.nuit_eur)} par nuit" if o.nuit_eur else ", sans frais de nuit")
    return (f"<b>Sur {o.plateforme}</b> : {html.escape(o.sous_jacent)} « {html.escape(o.instrument)} »\n"
            f"Acheter <b>{qte} {unite}</b>\n"
            f"Perte si le stop est touché : {euros(o.perte_au_stop_eur)}\n"
            f"Frais : {frais}")


def message_signal(s: Signal, p: Plan | None) -> str:
    gain = 100 * (s.objectif - s.entree) / s.entree
    lignes = [f"🟢 <b>ACHAT · {html.escape(s.nom)}</b>",
              f"{s.type_trading.capitalize()} · {NOMS_STRATEGIES.get(s.strategie, s.strategie)}",
              f"Signal à la clôture du {date_courte(s.date)}", ""]
    if p:
        h = p.entree_paris
        lignes.append(f"⏰ <b>Quand</b> : {date_courte(h)} à {h:%Hh%M} (heure de Paris), "
                      f"à l'ouverture de la {p.bourse}")
    lignes += [f"💰 <b>Entrée</b> : au prix du marché, vers {nombre(s.entree)}",
               f"🛑 <b>Stop</b> : {nombre(s.stop)} (−{nombre(s.risque_pct, 1)} %)",
               f"🎯 <b>Objectif</b> : {nombre(s.objectif)} (+{nombre(gain, 1)} %)",
               f"⚖️ <b>Gain/perte</b> : {nombre(s.ratio, 1)} pour 1"]
    if p:
        lignes += ["", "\n\n".join(_ordre(o) for o in p.ordres)]
    return "\n".join(lignes)


def message_bilan(signaux: list[Signal], clotures: list[dict], bilan: dict, seance) -> str:
    n = len(signaux)
    lignes = [f"📊 <b>Bilan au {date_courte(seance)}</b>",
              f"{n} nouveau{'x' if n > 1 else ''} signa{'ux' if n > 1 else 'l'}"]
    for c in clotures:
        icone = "✅" if c["statut"] == "succès" else "❌"
        lignes.append(f"{icone} {html.escape(str(c['nom']))} : {c['statut']} ({c['motif']}), "
                      f"{'+' if float(c['r']) >= 0 else ''}{nombre(float(c['r']), 1)} R")
    taux = f"{nombre(bilan['taux_reussite'], 0)} %" if bilan["taux_reussite"] is not None else "pas encore de résultat"
    lignes += ["",
               f"Depuis le début : {bilan['succes']} succès, {bilan['echecs']} échecs (réussite : {taux})",
               f"Résultat cumulé : {'+' if bilan['r_total'] >= 0 else ''}{nombre(bilan['r_total'], 1)} R",
               f"En cours : {bilan['ouverts']} ouverts, {bilan['en_attente']} en attente d'entrée",
               "",
               "<i>Simulation, pas un conseil. Frais de nuit estimés. "
               "Vérifiez la taille minimale de contrat sur IG.</i>"]
    return "\n".join(lignes)


def messages(signaux: list[Signal], clotures: list[dict], bilan: dict, seance,
             plans: dict | None = None) -> list[str]:
    plans = plans or {}
    return [message_signal(s, plans.get(id(s))) for s in signaux] + [message_bilan(signaux, clotures, bilan, seance)]


def send_telegram(textes: list[str]) -> bool:
    token, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    for texte in textes:
        r = httpx.post(f"https://api.telegram.org/bot{token}/sendMessage",
                       data={"chat_id": chat, "text": texte[:4000], "parse_mode": "HTML"}, timeout=15)
        r.raise_for_status()
    return True
