"""Commentaire IA du rapport horaire, par un modèle local (Ollama, ou LiteLLM devant Ollama).

Le modèle ne calcule rien et ne décide rien : il reçoit les chiffres déjà calculés et les décrit en quelques
lignes. Chaque nombre de sa réponse est vérifié contre ces chiffres ; au moindre nombre inventé, le
commentaire est retiré. Sans IA_URL, rien n'est appelé.

Variables : IA_URL (ex. http://192.168.56.1:11434, API compatible OpenAI), IA_MODELE (défaut qwen2.5:3b),
IA_CLE (facultatif, pour LiteLLM).
"""
from __future__ import annotations

import json
import os
import re

import httpx

CONSIGNE = """Tu es l'assistant de marché d'un particulier qui trade le DAX, le Nasdaq 100 et le S&P 500.
On te donne des chiffres déjà calculés. Écris en français 3 à 5 phrases courtes, une par ligne, sans titre :
ce qui a bougé depuis une heure, où en est le plan du jour, le niveau le plus proche à surveiller.
Règles strictes :
- utilise uniquement les nombres présents dans les données, arrondis à l'unité, jamais de calcul ni de pourcentage ;
- parle en points ;
- ne donne aucun conseil d'achat ou de vente et n'invente aucun niveau ;
- si rien n'a bougé, dis-le en une phrase."""

SEUIL_LIBRE = 5  # les petits nombres (« 3 phrases », « 1 heure ») ne sont pas vérifiés


def donnees(resumes: dict[str, dict]) -> dict:
    """Chiffres arrondis transmis au modèle (rien d'autre)."""
    out = {}
    for r in resumes.values():
        if "prix" not in r:
            continue
        x = {"cours": round(r["prix"]), "heure": r["heure"], "plus_haut_jour": round(r["haut"]),
             "plus_bas_jour": round(r["bas"])}
        if "var" in r:
            x["ecart_veille_pts"] = round(r["var"])
        if "var_1h" in r:
            x["ecart_1h_pts"] = round(r["var_1h"])
        if "etat" in r:
            x["plan"] = r["etat"].replace(" ", " ")
        if r.get("ordres") and r.get("trade") is None:
            x["niveaux_du_plan"] = [{"sens": "achat" if o["sens"] > 0 else "vente", "niveau": round(o["niveau"]),
                                     "distance_pts": round(abs(o["distance"]))} for o in r["ordres"]]
        if "rsi" in r:
            x["tendance"], x["rsi_jour"] = r["tendance"], round(r["rsi"])
        out[r["nom"]] = x
    return out


def nombres(texte: str) -> list[float]:
    """Nombres d'un texte français : « 25 140 », « 1,5 », « −37 »."""
    t = texte.replace(" ", " ").replace(" ", " ")
    out = []
    for m in re.finditer(r"\d{1,3}(?: \d{3})+(?:,\d+)?|\d+(?:[,.]\d+)?", t):
        out.append(float(m.group().replace(" ", "").replace(",", ".")))
    return out


def verifier(texte: str, d: dict) -> list[float]:
    """Nombres du texte absents des données (à 1 point près). Liste vide = commentaire fiable."""
    connus = [abs(x) for x in nombres(json.dumps(d, ensure_ascii=False))]
    return [x for x in nombres(texte) if x > SEUIL_LIBRE and not any(abs(x - k) <= 1 for k in connus)]


def commenter(resumes: dict[str, dict]) -> str | None:
    url = os.getenv("IA_URL")
    if not url:
        return None
    d = donnees(resumes)
    if not d:
        return None
    entetes = {"Authorization": f"Bearer {os.environ['IA_CLE']}"} if os.getenv("IA_CLE") else {}
    try:
        r = httpx.post(url.rstrip("/") + "/v1/chat/completions", headers=entetes, timeout=120,
                       json={"model": os.getenv("IA_MODELE", "qwen2.5:3b"), "temperature": 0.2,
                             "messages": [{"role": "system", "content": CONSIGNE},
                                          {"role": "user", "content": json.dumps(d, ensure_ascii=False)}]})
        r.raise_for_status()
        texte = r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:  # l'IA ne bloque jamais le rapport
        print(f"IA indisponible : {e}")
        return None
    faux = verifier(texte, d)
    if faux:
        print(f"Commentaire IA retiré, nombres inventés : {faux}\n{texte}")
        return None
    return texte
