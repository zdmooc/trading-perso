"""Rapport HTML horaire DAX / Nasdaq 100 / S&P 500 : graphiques, niveaux du plan, état des signaux.

Lecture seule : aucun ordre. Les bougies du jour viennent d'IG (cours de tes barrières), le contexte
journalier (moyennes, RSI, pivots de la semaine) vient de Yahoo.
Quota IG : seulement les bougies du jour, environ 40 par passage.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd

from . import alerts, matin, plan
from .indicators import atr, rsi, sma

PLOTLY = "https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.2/plotly.min.js"
VERT, ROUGE, GRIS, BLEU, ORANGE = "#22a06b", "#e5484d", "#8b949e", "#4c8dff", "#f5a524"


# ---------- données ----------

def charger_jour(maintenant: pd.Timestamp) -> tuple[dict[str, pd.DataFrame], str]:
    """Bougies du jour : IG si possible, sinon Yahoo (bougies de 30 min)."""
    import time

    from .ig import IG
    from .ig_releve import PAUSE
    out = {}
    try:
        epics = json.loads(Path("reports/ig/epics.json").read_text(encoding="utf-8"))
        ig = IG()
        ig.connexion()
        jour = maintenant.normalize()
        # IG lit "from" et "to" à l'heure du compte (Paris), pas en UTC.
        fin = (maintenant + pd.Timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        for s, info in plan.INDICES.items():
            debut = jour + pd.Timedelta(hours=info["heures"][0] - 1)
            try:
                out[s] = plan.barres_ig(ig.historique(epics[info["ig"]], debut.strftime("%Y-%m-%dT%H:%M:%S"),
                                                      fin, info.get("resolution", "HOUR")))
            except Exception as e:
                print(f"IG {info['ig']} : {e}")
            time.sleep(PAUSE)
    except Exception as e:  # pas d'accès IG : on se rabat sur Yahoo
        print(f"IG indisponible : {e}")
    manquants = [s for s in plan.INDICES if not len(out.get(s, []))]
    if manquants:
        for s, df in matin.telecharger(manquants, "2d", "30m").items():
            out[s] = df[df.index.date == maintenant.date()]
    return out, "IG" if len(manquants) < len(plan.INDICES) else "Yahoo"


def pivots_semaine(d: pd.DataFrame, jour) -> dict[str, float]:
    """Pivots classiques calculés sur la semaine précédente."""
    lundi = pd.Timestamp(jour) - pd.Timedelta(days=pd.Timestamp(jour).weekday())
    dates = pd.Index(d.index.date)
    w = d[(dates < lundi.date()) & (dates >= (lundi - pd.Timedelta(days=7)).date())]
    if not len(w):
        return {}
    hi, lo, cl = float(w["High"].max()), float(w["Low"].min()), float(w["Close"].iloc[-1])
    p = (hi + lo + cl) / 3
    return {"R2": p + hi - lo, "R1": 2 * p - lo, "P": p, "S1": 2 * p - hi, "S2": p - (hi - lo)}


def resume(s: str, jour_df: pd.DataFrame, d: pd.DataFrame | None, pl: dict | None, maintenant: pd.Timestamp) -> dict:
    """Chiffres clés d'un indice pour la carte du rapport."""
    info = plan.INDICES[s]
    r = {"nom": info["nom"], "drapeau": info["drapeau"], "taille": info["taille"]}
    if len(jour_df):
        r["prix"] = float(jour_df["Close"].iloc[-1])
        r["heure"] = f"{jour_df.index[-1]:%Hh%M}"
        r["haut"], r["bas"] = float(jour_df["High"].max()), float(jour_df["Low"].min())
    if pl and "prix" in r:
        r["var"] = r["prix"] - pl["cloture"]
        r["var_pct"] = 100 * r["var"] / pl["cloture"]
        r["ordres"] = []
        for o in pl["ordres"]:
            stop, obj = o["niveau"] - o["sens"] * o["risque"], o["niveau"] + o["sens"] * plan.RATIO * o["risque"]
            r["ordres"].append({**o, "stop": stop, "objectif": obj, "distance": o["niveau"] - r["prix"]})
        ses = plan.seances(jour_df, info["heures"], info.get("debut_min", 0)).get(maintenant.date())
        fin = maintenant.normalize() + pd.Timedelta(hours=info["heures"][1] + 1)
        if ses is not None and len(ses):
            t = plan.rejouer(ses, [plan.Ordre(**o) for o in pl["ordres"]], info["fin_entree"], info["spread"], maintenant >= fin)
            r["etat"] = plan.ligne_trade(t, info["taille"], maintenant >= fin)
            r["trade"] = t
        else:
            r["etat"] = "séance pas encore ouverte" if maintenant < fin else "pas de séance aujourd'hui"
    if d is not None and len(d) > 60:
        c = d["Close"]
        r["rsi"] = float(rsi(c, 14).iloc[-1])
        r["mm20"], r["mm50"] = float(sma(c, 20).iloc[-1]), float(sma(c, 50).iloc[-1])
        r["atr"] = float(atr(d).iloc[-1])
        r["tendance"] = "haussière" if c.iloc[-1] > r["mm20"] > r["mm50"] else \
            "baissière" if c.iloc[-1] < r["mm20"] < r["mm50"] else "sans direction nette"
        r["pivots"] = pivots_semaine(d, maintenant.date())
    return r


# ---------- graphiques (Plotly, sans dépendance Python) ----------

def _bougies(df: pd.DataFrame, nom: str, fmt: str = "%Y-%m-%d") -> dict:
    return {"type": "candlestick", "name": nom, "x": [t.strftime(fmt) for t in df.index],
            "open": df["Open"].round(1).tolist(), "high": df["High"].round(1).tolist(),
            "low": df["Low"].round(1).tolist(), "close": df["Close"].round(1).tolist(),
            "increasing": {"line": {"color": VERT}}, "decreasing": {"line": {"color": ROUGE}}, "showlegend": False}


def _ligne(y: float, couleur: str, texte: str, tirets: str = "dash") -> tuple[dict, dict]:
    forme = {"type": "line", "xref": "paper", "x0": 0, "x1": 1, "y0": y, "y1": y,
             "line": {"color": couleur, "width": 1.3, "dash": tirets}}
    note = {"xref": "paper", "x": 1, "y": y, "xanchor": "left", "text": f"{texte} {alerts.nombre(y, 0)}",
            "showarrow": False, "font": {"size": 10, "color": couleur}}
    return forme, note


def figure_jour(df: pd.DataFrame, r: dict) -> dict:
    formes, notes = [], []
    for o in r.get("ordres", []):
        achat = o["sens"] > 0
        for y, c, t, tir in ((o["niveau"], VERT if achat else ROUGE, "Achat" if achat else "Vente", "solid"),
                             (o["stop"], GRIS, "stop", "dot"), (o["objectif"], BLEU, "objectif", "dot")):
            f, n = _ligne(y, c, t, tir)
            formes.append(f)
            notes.append(n)
    if len(df):
        bas, haut = df["Low"].min(), df["High"].max()
        marge = (haut - bas) * 0.6 + 1
        for k, y in r.get("pivots", {}).items():
            if bas - marge <= y <= haut + marge:  # on n'affiche que les pivots proches du cours
                f, n = _ligne(y, ORANGE, k, "dashdot")
                formes.append(f)
                notes.append(n)
    t = r.get("trade")
    if t is not None and t.heure:
        h, _, m = t.heure.partition("h")
        notes.append({"x": f"{int(h):02d}:{m or '00'}", "y": t.entree, "text": "▶ entrée",
                      "showarrow": True, "arrowcolor": VERT if t.sens > 0 else ROUGE, "font": {"size": 11}})
    return {"data": [_bougies(df, r["nom"], "%H:%M")] if len(df) else [],
            "layout": {"shapes": formes, "annotations": notes, "margin": {"l": 50, "r": 90, "t": 10, "b": 30},
                       "height": 380, "xaxis": {"rangeslider": {"visible": False}, "type": "category", "nticks": 8},
                       "dragmode": "pan"}}


def figure_mois(d: pd.DataFrame, r: dict) -> dict:
    d6 = d.iloc[-130:]
    c = d["Close"]
    x = [f"{t:%Y-%m-%d}" for t in d6.index]
    traces = [_bougies(d6, r["nom"])]
    for n, coul in ((20, BLEU), (50, ORANGE)):
        traces.append({"type": "scatter", "mode": "lines", "name": f"moyenne {n} j", "x": x,
                       "y": sma(c, n).iloc[-130:].round(1).tolist(), "line": {"color": coul, "width": 1.5}})
    return {"data": traces, "layout": {"margin": {"l": 50, "r": 10, "t": 10, "b": 30}, "height": 300,
                                       "xaxis": {"rangeslider": {"visible": False}}, "legend": {"orientation": "h", "y": 1.08},
                                       "dragmode": "pan"}}


# ---------- page ----------

def _signe(x: float) -> str:
    return "pos" if x >= 0 else "neg"


def carte(s: str, r: dict) -> str:
    e = html.escape
    lignes = []
    if "prix" in r:
        var = ""
        if "var" in r:
            var = (f'<span class="{_signe(r["var"])}">{plan.pts(r["var"])} '
                   f'({"+" if r["var_pct"] >= 0 else "−"}{alerts.nombre(abs(r["var_pct"]), 2)} %)</span> depuis la clôture d\'hier')
        lignes.append(f'<p class="prix">{alerts.nombre(r["prix"], 0)} <small>à {r["heure"]}</small></p><p>{var}</p>')
        lignes.append(f'<p class="muted">Plus haut du jour {alerts.nombre(r["haut"], 0)} · plus bas {alerts.nombre(r["bas"], 0)}</p>')
    if "etat" in r:
        t = r.get("trade")
        cls = "" if t is None else ("pos" if t.pts >= 0 else "neg")
        lignes.append(f'<p class="etat {cls}"><b>Plan du jour :</b> {e(r["etat"])}</p>')
    for o in r.get("ordres", []):
        achat = o["sens"] > 0
        dist = o["distance"]
        # Un seul trade par jour : la distance au niveau n'a de sens que tant que rien n'est déclenché.
        reste = "" if r.get("trade") is not None else \
            f' · niveau {alerts.nombre(abs(dist), 0)} pts {"au-dessus" if dist > 0 else "sous"} le cours'
        lignes.append(
            f'<p class="ordre"><span class="{"pos" if achat else "neg"}">{"Achat" if achat else "Vente"} '
            f'à {alerts.nombre(o["niveau"], 0)}</span>{reste}<br><span class="muted">stop {alerts.nombre(o["stop"], 0)} '
            f'({plan.eur(-o["risque"] * r["taille"])}) · objectif {alerts.nombre(o["objectif"], 0)} '
            f'({plan.eur(plan.RATIO * o["risque"] * r["taille"])})</span></p>')
    if "rsi" in r:
        rs = r["rsi"]
        zone = " (surachat)" if rs >= 70 else " (survente)" if rs <= 30 else ""
        lignes.append(f'<p class="muted">Tendance {r["tendance"]} · RSI jour {rs:.0f}{zone} · '
                      f'mouvement moyen d\'une journée {alerts.nombre(r["atr"], 0)} pts</p>')
    return (f'<section class="carte"><h2>{r["drapeau"]} {e(r["nom"])}</h2>{"".join(lignes)}'
            f'<h3>Aujourd\'hui</h3><div id="j-{s.strip("^")}" class="graphe"></div>'
            f'<h3>6 derniers mois</h3><div id="m-{s.strip("^")}" class="graphe"></div></section>')


CSS = """
:root{--bg:#f6f7f9;--carte:#fff;--texte:#1b1f24;--muted:#6b7280;--bord:#e5e7eb}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d1117;--carte:#161b22;--texte:#e6edf3;--muted:#8b949e;--bord:#30363d}}
:root[data-theme="dark"]{--bg:#0d1117;--carte:#161b22;--texte:#e6edf3;--muted:#8b949e;--bord:#30363d}
body{margin:0;background:var(--bg);color:var(--texte);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:8px 0 2px}h2{font-size:18px;margin:0 0 8px}h3{font-size:14px;color:var(--muted);margin:18px 0 4px}
.carte{background:var(--carte);border:1px solid var(--bord);border-radius:12px;padding:16px;margin:16px 0}
.prix{font-size:26px;font-weight:600;margin:0}.prix small{font-size:13px;color:var(--muted);font-weight:400}
p{margin:6px 0}.muted{color:var(--muted);font-size:13px}.pos{color:#22a06b}.neg{color:#e5484d}
.etat{padding:8px 10px;border-radius:8px;background:var(--bg)}.ordre{margin:10px 0}
.graphe{width:100%}.note{font-size:12px;color:var(--muted);margin-top:24px}
"""


def page(maintenant: pd.Timestamp, source: str, resumes: dict[str, dict], figures: dict[str, dict]) -> str:
    cartes = "".join(carte(s, r) for s, r in resumes.items())
    js = json.dumps(figures, separators=(",", ":"), default=float)
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Marché heure par heure</title><style>{CSS}</style><script src="{PLOTLY}"></script></head>
<body><main>
<h1>Marché à {maintenant:%Hh%M}</h1>
<p class="muted">{alerts.date_fr(maintenant.date())} · cours du jour {source} · lecture seule, aucun ordre passé</p>
{cartes}
<p class="note">Lignes pleines : entrées du plan de 8h45. Pointillés gris : stops. Pointillés bleus : objectifs (3 fois le risque).
Orange : pivots de la semaine (calculés sur Yahoo, quelques points d'écart possibles avec IG).
Les montants en € sont pour la taille du plan (DAX et Nasdaq 0,5 contrat, S&P 500 1 contrat).</p>
</main>
<script>
const F={js};
const sombre=matchMedia('(prefers-color-scheme: dark)').matches;
const coul=sombre?'#e6edf3':'#1b1f24',grille=sombre?'#30363d':'#e5e7eb';
for(const [id,f] of Object.entries(F)){{
  const l=Object.assign({{separators:', ',paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{{color:coul,size:11}}}},f.layout);
  l.xaxis=Object.assign({{gridcolor:grille}},l.xaxis);l.yaxis=Object.assign({{gridcolor:grille,tickformat:',.0f'}},l.yaxis||{{}});
  Plotly.newPlot(id,f.data,l,{{responsive:true,displayModeBar:false,scrollZoom:true}});
}}
</script></body></html>
"""


def executer(out: Path, telegram: bool = True) -> Path:
    maintenant = pd.Timestamp.now(tz=matin.PARIS)
    jour, source = charger_jour(maintenant)
    d = matin.telecharger(plan.INDICES, "1y", "1d")
    chemin_plan = plan.dossier(out) / f"plan_{maintenant.date()}.json"
    pl = json.loads(chemin_plan.read_text(encoding="utf-8"))["indices"] if chemin_plan.exists() else {}
    resumes, figures = {}, {}
    for s in plan.INDICES:
        df = jour.get(s, pd.DataFrame(columns=["Open", "High", "Low", "Close"]))
        r = resume(s, df, d.get(s), pl.get(s), maintenant)
        resumes[s] = r
        figures[f"j-{s.strip('^')}"] = figure_jour(df, r)
        if s in d:
            figures[f"m-{s.strip('^')}"] = figure_mois(d[s], r)
    rep = out / "html"
    rep.mkdir(parents=True, exist_ok=True)
    chemin = rep / "marche.html"
    chemin.write_text(page(maintenant, source, resumes, figures), encoding="utf-8")
    print(f"Rapport écrit : {chemin}")
    if telegram:
        legende = " · ".join(f"{r['nom']} {alerts.nombre(r['prix'], 0)}" for r in resumes.values() if "prix" in r)
        alerts.send_document(str(chemin), f"📈 Marché à {maintenant:%Hh%M}\n{legende}", silencieux=True)
    return chemin
