"""Client minimal de l'API REST IG (compte démo par défaut). Les accès viennent des secrets GitHub."""
from __future__ import annotations

import os

import httpx

URLS = {"DEMO": "https://demo-api.ig.com/gateway/deal", "LIVE": "https://api.ig.com/gateway/deal"}


class IG:
    def __init__(self, cle: str | None = None, identifiant: str | None = None, mot_de_passe: str | None = None,
                 type_compte: str | None = None):
        self.type = (type_compte or os.environ.get("IG_ACC_TYPE", "DEMO")).upper()
        if self.type != "DEMO":
            raise RuntimeError("Par sécurité, seul le compte DEMO est autorisé.")
        self.base = URLS[self.type]
        self.cle = cle or os.environ["IG_API_KEY"]
        self._login = (identifiant or os.environ["IG_USERNAME"], mot_de_passe or os.environ["IG_PASSWORD"])
        self.client = httpx.Client(timeout=30)
        self.entetes = {"X-IG-API-KEY": self.cle, "Accept": "application/json; charset=UTF-8",
                        "Content-Type": "application/json; charset=UTF-8"}

    def _req(self, methode: str, chemin: str, version: int = 1, **kw) -> dict:
        r = self.client.request(methode, self.base + chemin, headers={**self.entetes, "Version": str(version)}, **kw)
        if r.status_code >= 400:
            raise RuntimeError(f"IG {methode} {chemin} : {r.status_code} {r.text[:200]}")
        return r.json() if r.content else {}

    def connexion(self) -> dict:
        r = self.client.post(self.base + "/session", headers={**self.entetes, "Version": "2"},
                             json={"identifier": self._login[0], "password": self._login[1]})
        if r.status_code >= 400:
            raise RuntimeError(f"Connexion IG refusée : {r.status_code} {r.text[:200]}")
        self.entetes["CST"] = r.headers["CST"]
        self.entetes["X-SECURITY-TOKEN"] = r.headers["X-SECURITY-TOKEN"]
        return r.json()

    def comptes(self) -> list[dict]:
        return self._req("GET", "/accounts")["accounts"]

    def chercher(self, terme: str) -> list[dict]:
        return self._req("GET", "/markets", params={"searchTerm": terme}).get("markets", [])

    def marche(self, epic: str) -> dict:
        return self._req("GET", f"/markets/{epic}", version=3)

    def positions(self) -> list[dict]:
        return self._req("GET", "/positions", version=2).get("positions", [])
