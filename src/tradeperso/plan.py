"""Plan du jour sur 3 indices (DAX 40, Nasdaq 100, S&P 500), en cours IG. Aucun ordre n'est passé.

- 8h45 : le plan (2 entrées au plus par indice). Il ne change pas de la journée.
- 14h15 : point avant l'ouverture américaine (plan inchangé, seulement l'état des entrées).
- 17h45 : bilan du DAX. Les indices américains finissent à 22h : leur résultat arrive le lendemain matin.

Pour chaque indice, la règle retenue est la meilleure de quelques règles simples sur les niveaux de la séance
de la veille, testées sur 2 ans de bougies horaires (Yahoo). Objectif toujours à 3 fois le risque.
Hypothèses prudentes du test : dans la bougie d'entrée, le stop compte si la bougie clôture au-delà ;
ensuite, si stop et objectif tombent dans la même bougie, on compte le stop.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import alerts, matin
from .indicators import atr, sma

INDICES = {
    "^GDAXI": dict(nom="DAX 40", ig="Germany 40", drapeau="🇩🇪", heures=(9, 17), fin_entree=15, taille=0.5,
                   spread=1.2, fenetre="entrée 9h-16h, tout fermé à 17h30"),
    "^NDX": dict(nom="Nasdaq 100", ig="US Tech 100", drapeau="🇺🇸", heures=(15, 21), fin_entree=20, taille=0.5,
                 spread=1.0, fenetre="entrée 15h30-21h, tout fermé à 22h"),
    "^GSPC": dict(nom="S&P 500", ig="US 500", drapeau="🇺🇸", heures=(15, 21), fin_entree=20, taille=1.0,
                  spread=0.4, fenetre="entrée 15h30-21h, tout fermé à 22h"),
}
RATIO = 3.0
MIN_TRADES = 30


@dataclass(frozen=True)
class Regle:
    type: str      # "cassure" (on suit la sortie du range de la veille) ou "rejet" (on joue le retour)
    k_stop: float  # stop à k_stop ATR journalier de l'entrée
    filtre: str    # "aucun" ou "tendance" (seulement dans le sens de la moyenne 20 jours)

    @property
    def cle(self) -> str:
        return f"{self.type}-{self.k_stop}-{self.filtre}"

    @property
    def nom(self) -> str:
        t = "Cassure du plus haut / plus bas de la veille" if self.type == "cassure" else \
            "Rejet sur le plus haut / plus bas de la veille"
        return t + (", dans le sens de la tendance" if self.filtre == "tendance" else "") + f", stop {self.k_stop} ATR"


REGLES = [Regle(t, k, f) for t in ("cassure", "rejet") for k in (0.25, 0.4, 0.6) for f in ("aucun", "tendance")]
PAR_CLE = {r.cle: r for r in REGLES}


@dataclass
class Ordre:
    sens: int      # 1 achat, -1 vente
    niveau: float
    cote: str      # "haut" : déclenché si le cours monte jusqu'au niveau ; "bas" : s'il descend
    risque: float  # en points


@dataclass
class Trade:
    sens: int
    entree: float
    stop: float
    objectif: float
    sortie: float = np.nan
    motif: str = ""
    heure: str = ""
    pts: float = np.nan


def ordres(regle: Regle, haut: float, bas: float, a: float, tendance: int) -> list[Ordre]:
    r = regle.k_stop * a
    if regle.type == "cassure":
        liste = [Ordre(1, haut + 0.1 * a, "haut", r), Ordre(-1, bas - 0.1 * a, "bas", r)]
    else:
        liste = [Ordre(-1, haut, "haut", r), Ordre(1, bas, "bas", r)]
    if regle.filtre == "tendance":
        liste = [o for o in liste if o.sens == tendance]
    return liste


def rejouer(barres: pd.DataFrame, liste: list[Ordre], fin_entree: int, spread: float, fini: bool = True) -> Trade | None:
    """Rejoue une séance (bougies horaires, heure de Paris). Un seul trade : le premier niveau touché."""
    pos = None
    for b in barres.itertuples():
        if pos is None:
            if b.Index.hour > fin_entree:
                continue
            touches = [o for o in liste if (b.High >= o.niveau if o.cote == "haut" else b.Low <= o.niveau)]
            if not touches:
                continue
            o = min(touches, key=lambda o: abs(b.Open - o.niveau))
            entree = max(b.Open, o.niveau) if o.cote == "haut" else min(b.Open, o.niveau)
            pos = Trade(o.sens, entree, entree - o.sens * o.risque, entree + o.sens * RATIO * o.risque,
                        heure=f"{b.Index:%Hh}")
            if (b.Close <= pos.stop) if o.sens > 0 else (b.Close >= pos.stop):
                pos.sortie, pos.motif = pos.stop, "stop"
                break
            continue
        if (b.Low <= pos.stop) if pos.sens > 0 else (b.High >= pos.stop):
            pos.sortie, pos.motif = pos.stop, "stop"
            break
        if (b.High >= pos.objectif) if pos.sens > 0 else (b.Low <= pos.objectif):
            pos.sortie, pos.motif = pos.objectif, "objectif"
            break
    if pos is None:
        return None
    if pos.motif == "":
        pos.sortie, pos.motif = float(barres["Close"].iloc[-1]), ("clôture" if fini else "en cours")
    pos.pts = pos.sens * (pos.sortie - pos.entree) - spread
    return pos


def seances(h: pd.DataFrame, heures: tuple[int, int]) -> dict:
    s = h[(h.index.hour >= heures[0]) & (h.index.hour <= heures[1])]
    return {d: g for d, g in s.groupby(s.index.date)}


def contexte(d: pd.DataFrame) -> pd.DataFrame:
    """ATR et tendance (moyenne 20 jours) de chaque jour, indexés par date."""
    c = pd.DataFrame({"atr": atr(d), "tendance": np.where(d["Close"] > sma(d["Close"], 20), 1, -1)})
    c.index = pd.Index(d.index.date)
    return c.dropna()


def backtest(h: pd.DataFrame, d: pd.DataFrame, info: dict) -> dict[str, list[float]]:
    """Points gagnés ou perdus par trade, pour chaque règle."""
    ses, ctx = seances(h, info["heures"]), contexte(d)
    jours = sorted(ses)
    res = {r.cle: [] for r in REGLES}
    for veille, jour in zip(jours, jours[1:]):
        if veille not in ctx.index:
            continue
        g, c = ses[veille], ctx.loc[veille]
        for r in REGLES:
            t = rejouer(ses[jour], ordres(r, float(g["High"].max()), float(g["Low"].min()), float(c["atr"]),
                                          int(c["tendance"])), info["fin_entree"], info["spread"])
            if t is not None:
                res[r.cle].append(round(t.pts, 1))
    return res


def stats(pts: list[float], taille: float) -> dict:
    p = np.array(pts, dtype=float)
    if not len(p):
        return {"trades": 0}
    g, l = p[p > 0], p[p <= 0]
    return {"trades": len(p), "gagnes_pct": round(100 * len(g) / len(p)), "gain_moy": round(float(g.mean())) if len(g) else 0,
            "perdus_pct": round(100 * len(l) / len(p)), "perte_moy": round(float(l.mean())) if len(l) else 0,
            "total_pts": round(float(p.sum())), "total_eur": round(float(p.sum()) * taille)}


def meilleure(res: dict[str, list[float]], taille: float) -> str:
    ok = {k: stats(v, taille) for k, v in res.items() if len(v) >= MIN_TRADES}
    return max(ok, key=lambda k: ok[k]["total_pts"]) if ok else REGLES[0].cle


# ---------- formats ----------

def pts(x: float) -> str:
    return ("+" if x >= 0 else "−") + alerts.nombre(abs(x), 0) + " pts"


def eur(x: float) -> str:
    return ("+" if x >= 0 else "−") + alerts.nombre(abs(x), 0) + " €"


def depuis(st: dict) -> str:
    if not st.get("debut"):
        return "📊 Test"
    d = pd.Timestamp(st["debut"])
    return f"📊 Test depuis {alerts.MOIS_COURTS[d.month - 1]} {d.year}"


def ligne_stats(s: dict, prefixe: str = "📊 2 ans") -> str:
    if not s.get("trades"):
        return f"{prefixe} : aucun trade"
    return (f"{prefixe} : {s['trades']} trades · {s['gagnes_pct']} % gagnés ({pts(s['gain_moy'])} en moy.) · "
            f"{s['perdus_pct']} % perdus ({pts(s['perte_moy'])} en moy.) · total {pts(s['total_pts'])} = {eur(s['total_eur'])}")


def ligne_ordre(o: Ordre, taille: float) -> str:
    stop, obj = o.niveau - o.sens * o.risque, o.niveau + o.sens * RATIO * o.risque
    return (f"{'🟢 Achat' if o.sens > 0 else '🔴 Vente'} si {alerts.nombre(o.niveau, 0)} touché\n"
            f"   stop {alerts.nombre(stop, 0)} ({pts(-o.risque)} = {eur(-o.risque * taille)}) · "
            f"objectif {alerts.nombre(obj, 0)} ({pts(RATIO * o.risque)} = {eur(RATIO * o.risque * taille)})")


def ligne_trade(t: Trade | None, taille: float, fini: bool) -> str:
    if t is None:
        return "pas déclenché" + ("" if fini else " pour l'instant")
    sens = "achat" if t.sens > 0 else "vente"
    etat = {"stop": "stoppé", "objectif": "objectif atteint ✅", "clôture": "fermé en fin de séance",
            "en cours": "en cours"}[t.motif]
    return f"{sens} à {alerts.nombre(t.entree, 0)} ({t.heure}), {etat} : {pts(t.pts)} = {eur(t.pts * taille)}"


# ---------- données ----------

def barres_ig(prix: list[dict]) -> pd.DataFrame:
    """Bougies IG (prix milieu entre vente et achat), index en heure de Paris."""
    lignes = []
    for p in prix:
        m = {k: (p[k + "Price"]["bid"] + p[k + "Price"]["ask"]) / 2 for k in ("open", "high", "low", "close")
             if p.get(k + "Price", {}).get("bid") is not None and p[k + "Price"].get("ask") is not None}
        if len(m) == 4:
            lignes.append({"t": pd.Timestamp(p["snapshotTimeUTC"], tz="UTC"), "Open": m["open"], "High": m["high"],
                           "Low": m["low"], "Close": m["close"]})
    if not lignes:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close"])
    df = pd.DataFrame(lignes).set_index("t").sort_index()
    df.index = df.index.tz_convert(matin.PARIS)
    return df


def charger_ig(maintenant: pd.Timestamp, jours: int = 5) -> dict[str, pd.DataFrame]:
    """Bougies horaires IG des derniers jours pour les 3 indices (lecture seule). Vide si IG ne répond pas."""
    import time

    from .ig import IG
    from .ig_releve import PAUSE
    epics = json.loads(Path("reports/ig/epics.json").read_text(encoding="utf-8"))
    out = {}
    try:
        ig = IG()
        ig.connexion()
    except Exception as e:  # pas d'accès IG : on se rabat sur Yahoo
        print(f"IG indisponible : {e}")
        return out
    debut = (maintenant.tz_convert("UTC") - pd.Timedelta(days=jours)).strftime("%Y-%m-%dT00:00:00")
    fin = (maintenant.tz_convert("UTC") + pd.Timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    for s, info in INDICES.items():
        try:
            out[s] = barres_ig(ig.historique(epics[info["ig"]], debut, fin))
        except Exception as e:
            print(f"IG {info['ig']} : {e}")
        time.sleep(PAUSE)
    return out


# ---------- plan, journal, messages ----------

def dossier(out: Path) -> Path:
    d = out / "plan"
    d.mkdir(parents=True, exist_ok=True)
    return d


def charger_stats(out: Path, d: dict, h: dict) -> dict:
    """Backtest de toutes les règles (une fois par jour, mis en cache)."""
    chemin = dossier(out) / "stats.json"
    aujourd_hui = str(pd.Timestamp.now(tz=matin.PARIS).date())
    if chemin.exists():
        cache = json.loads(chemin.read_text(encoding="utf-8"))
        if cache.get("date") == aujourd_hui and "debut" in cache:
            return cache
    debuts = [h[s].index[0] for s in INDICES if s in h and len(h[s])]
    cache = {"date": aujourd_hui, "debut": str(min(debuts).date()) if debuts else aujourd_hui, "indices": {}}
    for s, info in INDICES.items():
        if s not in h or s not in d:
            continue
        res = backtest(h[s], d[s], info)
        cle = meilleure(res, info["taille"])
        cache["indices"][s] = {"choisie": cle, "regles": {k: stats(v, info["taille"]) for k, v in res.items()}}
    chemin.write_text(json.dumps(cache, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return cache


def preparer(maintenant: pd.Timestamp, st: dict, d: dict, h: dict, ig: dict) -> dict:
    """Niveaux du jour, calculés sur la dernière séance terminée (cours IG si possible)."""
    plan = {"date": str(maintenant.date()), "indices": {}}
    for s, info in INDICES.items():
        if s not in st["indices"] or s not in d:
            continue
        source = "IG" if len(ig.get(s, [])) else "Yahoo"
        ses = seances(ig[s] if source == "IG" else h[s], info["heures"])
        passees = [j for j in sorted(ses) if j < maintenant.date()]
        ctx = contexte(d[s])
        ctx = ctx[ctx.index < maintenant.date()]
        if not passees or ctx.empty:
            continue
        g = ses[passees[-1]]
        av = ses[passees[-2]] if len(passees) >= 2 else None
        regle = PAR_CLE[st["indices"][s]["choisie"]]
        c = ctx.iloc[-1]
        liste = ordres(regle, float(g["High"].max()), float(g["Low"].min()), float(c["atr"]), int(c["tendance"]))
        plan["indices"][s] = {
            "source": source, "regle": regle.cle, "veille": str(passees[-1]),
            "cloture": float(g["Close"].iloc[-1]),
            "variation": float(g["Close"].iloc[-1] - av["Close"].iloc[-1]) if av is not None else None,
            "ordres": [o.__dict__ for o in liste],
        }
    return plan


def evaluer(plan: dict, barres: dict, maintenant: pd.Timestamp) -> dict[str, tuple[Trade | None, bool]]:
    """Résultat de chaque indice du plan sur la séance du jour du plan."""
    jour = pd.Timestamp(plan["date"]).date()
    out = {}
    for s, p in plan["indices"].items():
        info = INDICES[s]
        df = barres.get(s)
        if df is None or not len(df):
            continue
        ses = seances(df, info["heures"]).get(jour)
        fin = pd.Timestamp(jour, tz=matin.PARIS) + pd.Timedelta(hours=info["heures"][1] + 1)
        fini = maintenant >= fin
        if ses is None or not len(ses):
            out[s] = (None, fini)
            continue
        liste = [Ordre(**o) for o in p["ordres"]]
        out[s] = (rejouer(ses, liste, info["fin_entree"], info["spread"], fini), fini)
    return out


COLONNES = ["date", "indice", "regle", "source", "sens", "entree", "heure", "stop", "objectif", "sortie", "motif", "pts",
            "euros", "statut"]


def journal_maj(chemin: Path, plan: dict, res: dict) -> pd.DataFrame:
    j = pd.read_csv(chemin) if chemin.exists() else pd.DataFrame(columns=COLONNES)
    for s, (t, fini) in res.items():
        info, p = INDICES[s], plan["indices"][s]
        ligne = {"date": plan["date"], "indice": info["nom"], "regle": p["regle"], "source": p["source"]}
        if t is None:
            ligne["statut"] = "non déclenché" if fini else "en attente"
        else:
            ligne.update(sens="achat" if t.sens > 0 else "vente", entree=round(t.entree, 1), heure=t.heure,
                         stop=round(t.stop, 1), objectif=round(t.objectif, 1), sortie=round(t.sortie, 1), motif=t.motif,
                         pts=round(t.pts, 1), euros=round(t.pts * info["taille"], 1),
                         statut="en cours" if t.motif == "en cours" else ("gagné" if t.pts > 0 else "perdu"))
        j = j[~((j["date"] == plan["date"]) & (j["indice"] == info["nom"]))]
        j = pd.concat([j, pd.DataFrame([ligne])], ignore_index=True)
    j = j.sort_values(["date", "indice"])[COLONNES]
    j.to_csv(chemin, index=False)
    return j


def stats_reelles(j: pd.DataFrame, nom: str, taille: float) -> dict:
    f = j[(j["indice"] == nom) & j["statut"].isin(["gagné", "perdu"])]
    return stats(f["pts"].astype(float).tolist(), taille)


def message_plan(plan: dict, st: dict, j: pd.DataFrame, hier: list[str], long_terme: list[str] | None = None) -> str:
    """Une ligne vide entre chaque bloc : plus lisible sur téléphone."""
    jour = pd.Timestamp(plan["date"])
    l = [f"📋 <b>Plan du jour · {alerts.date_courte(jour)}</b> (cours IG)", "", "Hors plan = pas de trade."]
    if hier:
        l += ["", "", "<b>Hier</b>"]
        for x in hier:
            l += ["", x]
    for s, p in plan["indices"].items():
        info = INDICES[s]
        var = f" ({pts(p['variation'])})" if p.get("variation") is not None else ""
        l += ["", "", f"{info['drapeau']} <b>{info['nom']}</b> · veille {alerts.nombre(p['cloture'], 0)}{var}"
                  + ("" if p["source"] == "IG" else " · ⚠️ cours Yahoo, IG indisponible")]
        for o in p["ordres"]:
            l += ["", ligne_ordre(Ordre(**o), info["taille"])]
        if not p["ordres"]:
            l += ["", "Aucune entrée aujourd'hui."]
        s2 = st["indices"][s]["regles"][p["regle"]]
        l += ["", ligne_stats(s2, depuis(st))]
        if s2.get("total_pts", 0) <= 0:
            l += ["⚠️ Règle perdante sur le test : pour info seulement, ne pas trader."]
        r = stats_reelles(j, info["nom"], info["taille"])
        if r.get("trades"):
            l += ["", ligne_stats(r, "📒 Plan réel")]
        t = f"{info['taille']:g}".replace(".", ",")
        l += ["", f"⏰ {info['fenetre']} · {t} contrat = {t} €/pt"]
    if long_terme:
        l += ["", "", "📈 <b>Long terme</b>"]
        for x in long_terme:
            l += ["", x]
    return "\n".join(l)


def long_terme(out: Path, zones: dict) -> list[str]:
    """Positions swing ouvertes (journal des signaux) et zones d'achat sur repli du Nasdaq."""
    lignes = []
    jr = out / "journal.csv"
    j = pd.read_csv(jr) if jr.exists() else pd.DataFrame()
    ouverts = j[j["statut"] == "ouvert"] if len(j) else j
    symboles = list(ouverts["symbole"]) if len(ouverts) else []
    symboles += [s for s in zones if s not in symboles]
    cours = {s: float(df["Close"].iloc[-1]) for s, df in matin.telecharger(symboles, "5d", "1d").items()}
    for r in ouverts.itertuples() if len(ouverts) else []:
        c = cours.get(r.symbole)
        if c is None:
            continue
        e = float(r.prix_entree)
        lignes.append(f"{r.nom} : acheté {alerts.nombre(e, 0 if e >= 1000 else 2)}, cours {alerts.nombre(c, 0 if c >= 1000 else 2)} "
                      f"({pts(c - e) if e >= 1000 else ('+' if c >= e else '−') + alerts.nombre(abs(c - e), 2) + ' $'})\n"
                      f"   stop {alerts.nombre(float(r.stop), 0 if e >= 1000 else 2)} · objectif {alerts.nombre(float(r.objectif), 0 if e >= 1000 else 2)}")
    for s, z in zones.items():
        c = cours.get(s)
        if c is None:
            continue
        for x in z.get("liste", []):
            lignes.append(f"🛒 {x['nom']} Nasdaq : achat {alerts.nombre(x['achat'], 0)} (à {pts(x['achat'] - c)})\n"
                          f"   stop {alerts.nombre(x['stop'], 0)} · objectif {alerts.nombre(x['objectif'], 0)}")
    return lignes


def message_suivi(titre: str, plan: dict, res: dict, ig: dict) -> str:
    l = [titre]
    for s, p in plan["indices"].items():
        l.append("")
        info = INDICES[s]
        cours = f" {alerts.nombre(float(ig[s]['Close'].iloc[-1]), 0)}" if len(ig.get(s, [])) else ""
        t, fini = res.get(s, (None, False))
        l.append(f"{info['drapeau']} <b>{info['nom']}</b>{cours} : {ligne_trade(t, info['taille'], fini)}")
    l += ["", "Le plan ne change pas."]
    return "\n".join(l)


def rapport(out: Path, plan: dict, st: dict, j: pd.DataFrame, texte: str) -> None:
    import re
    l = ["# Plan du jour", "", re.sub(r"</?b>", "**", texte).replace("\n", "  \n"), "", f"## Statistiques depuis le {st.get('debut', '?')} (bougies horaires)",
         "", "Points nets du spread IG. Objectif à 3 fois le risque. La règle retenue a le meilleur total.", ""]
    for s, info in INDICES.items():
        if s not in st["indices"]:
            continue
        l += [f"### {info['nom']} ({info['taille']:g} contrat)".replace(".", ","), "",
              "| Règle | Trades | Gagnés | Gain moyen | Perdus | Perte moyenne | Total |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for cle, s2 in st["indices"][s]["regles"].items():
            if not s2.get("trades"):
                continue
            nom = PAR_CLE[cle].nom + (" ✅" if cle == st["indices"][s]["choisie"] else "")
            l.append(f"| {nom} | {s2['trades']} | {s2['gagnes_pct']} % | {pts(s2['gain_moy'])} | {s2['perdus_pct']} % | "
                     f"{pts(s2['perte_moy'])} | {pts(s2['total_pts'])} = {eur(s2['total_eur'])} |")
        l.append("")
    l += ["## Journal réel du plan", "", *tableau(j.tail(30)), ""]
    (out / "plan_du_jour.md").write_text("\n".join(l), encoding="utf-8")


def tableau(j: pd.DataFrame) -> list[str]:
    if not len(j):
        return ["Aucun trade pour l'instant."]
    return ["| " + " | ".join(j.columns) + " |", "|" + " --- |" * len(j.columns)] + \
        ["| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |" for r in j.itertuples(index=False)]


def executer(out: Path, phase: str, telegram: bool = True) -> None:
    maintenant = pd.Timestamp.now(tz=matin.PARIS)
    rep = dossier(out)
    ig = charger_ig(maintenant)
    jr = rep / "journal.csv"
    j = pd.read_csv(jr) if jr.exists() else pd.DataFrame(columns=COLONNES)
    if phase == "plan":
        d = matin.telecharger(INDICES, "5y", "1d")
        h = matin.telecharger(INDICES, "730d", "1h")
        st = charger_stats(out, d, h)
        # Résultat final de la veille (les indices américains finissent à 22h).
        hier = []
        precedents = sorted(rep.glob("plan_*.json"))
        precedents = [p for p in precedents if p.stem[5:] < str(maintenant.date())]
        if precedents and ig:
            pv = json.loads(precedents[-1].read_text(encoding="utf-8"))
            res = evaluer(pv, ig, maintenant)
            j = journal_maj(jr, pv, res)
            hier = [f"{INDICES[s]['nom']} : {ligne_trade(t, INDICES[s]['taille'], f)}" for s, (t, f) in res.items()]
        plan = preparer(maintenant, st, d, h, ig)
        (rep / f"plan_{plan['date']}.json").write_text(json.dumps(plan, indent=1) + "\n", encoding="utf-8")
        try:
            import tomllib
            zones = tomllib.loads(Path("config.toml").read_text(encoding="utf-8")).get("zones", {})
            lt = long_terme(out, zones)
        except Exception as e:  # le long terme ne bloque jamais le plan
            print(f"Long terme : {e}")
            lt = []
        texte = message_plan(plan, st, j, hier, lt)
    else:
        chemin = rep / f"plan_{maintenant.date()}.json"
        if not chemin.exists():
            print("Pas de plan aujourd'hui.")
            return
        plan = json.loads(chemin.read_text(encoding="utf-8"))
        st = json.loads((rep / "stats.json").read_text(encoding="utf-8"))
        res = evaluer(plan, ig, maintenant)
        j = journal_maj(jr, plan, res)
        titre = "🕑 <b>Point de 14h15</b> (cours IG)" if phase == "point" else "🏁 <b>Bilan de 17h45</b> (cours IG)"
        texte = message_suivi(titre, plan, res, ig)
        if phase == "bilan":
            texte += "\nNasdaq et S&P 500 finissent à 22h : résultat demain matin."
    rapport(out, plan, st, j, texte)
    print(texte)
    if telegram:
        alerts.send_telegram([texte])
