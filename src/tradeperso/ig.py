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
        corps = {"identifier": self._login[0], "password": self._login[1]}
        r = self.client.post(self.base + "/session", headers={**self.entetes, "Version": "2"}, json=corps)
        if r.status_code == 403 and "stockbroking" in r.text:
            # Session v2 refusée si le compte par défaut est un compte actions : on tente la v3 (OAuth).
            r = self.client.post(self.base + "/session", headers={**self.entetes, "Version": "3"}, json=corps)
            if r.status_code < 400:
                d = r.json()
                self.entetes["Authorization"] = "Bearer " + d["oauthToken"]["access_token"]
                self.entetes["IG-ACCOUNT-ID"] = os.environ.get("IG_ACCOUNT_ID") or d["accountId"]
                return d
        if r.status_code >= 400:
            raise RuntimeError(f"Connexion IG refusée : {r.status_code} {r.text[:200]}")
        self.entetes["CST"] = r.headers["CST"]
        self.entetes["X-SECURITY-TOKEN"] = r.headers["X-SECURITY-TOKEN"]
        compte = os.environ.get("IG_ACCOUNT_ID")
        d = r.json()
        if compte and compte != d.get("currentAccountId"):
            self._req("PUT", "/session", json={"accountId": compte, "defaultAccount": False})
        return d

    def comptes(self) -> list[dict]:
        return self._req("GET", "/accounts")["accounts"]

    def chercher(self, terme: str) -> list[dict]:
        return self._req("GET", "/markets", params={"searchTerm": terme}).get("markets", [])

    def marche(self, epic: str) -> dict:
        return self._req("GET", f"/markets/{epic}", version=3)

    def historique(self, epic: str, debut: str, fin: str, resolution: str = "HOUR") -> list[dict]:
        """Bougies passées (lecture seule). Dates au format 2026-10-07T00:00:00. Consomme le quota hebdomadaire."""
        return self._req("GET", f"/prices/{epic}", version=3,
                         params={"resolution": resolution, "from": debut, "to": fin, "pageSize": 0}).get("prices", [])

    def positions(self) -> list[dict]:
        return self._req("GET", "/positions", version=2).get("positions", [])
