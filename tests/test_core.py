import numpy as np
import pandas as pd

from tradeperso import backtest
from tradeperso.indicators import rsi, sma
from tradeperso.scanner import scan, to_markdown
from tradeperso.strategies import STRATEGIES


def bars(close: np.ndarray) -> pd.DataFrame:
    idx = pd.bdate_range("2020-01-01", periods=len(close))
    return pd.DataFrame({"Open": close, "High": close * 1.01, "Low": close * 0.99, "Close": close}, index=idx)


def random_walk(n=1500, seed=1, drift=0.0005):
    rng = np.random.default_rng(seed)
    return bars(100 * np.exp(np.cumsum(rng.normal(drift, 0.012, n))))


def test_indicators():
    s = pd.Series(np.arange(1.0, 31.0))
    assert sma(s, 5).iloc[-1] == 28.0
    assert rsi(s, 2).iloc[-1] == 100.0


def test_strategies_produce_columns_and_trades():
    df = random_walk()
    for name, st in STRATEGIES.items():
        data = df if st.sens > 0 else random_walk(drift=-0.0005)
        out = st.fonction(data)
        assert {"entry", "stop", "target", "exit"} <= set(out.columns), name
        trades = backtest.run(out, "TEST", sens=st.sens, breakeven_r=1.0)
        assert trades, f"{name} n'a produit aucun trade"
        for t in trades:
            assert t.sortie_date > t.entree_date or t.motif in {"stop", "objectif"}
            assert (t.stop < t.entree) if st.sens > 0 else (t.stop > t.entree)
            assert t.r >= -3  # un écart à l'ouverture peut dépasser 1 R


def test_stop_hit_gives_about_minus_one_r():
    df = bars(np.full(10, 100.0))
    df["entry"] = [True] + [False] * 9
    df["stop"], df["target"], df["exit"] = 95.0, np.nan, False
    df.loc[df.index[3], "Low"] = 90.0
    (t,) = backtest.run(df, frais_bps=0)
    assert t.motif == "stop" and t.sortie == 95.0 and round(t.r, 6) == -1.0


def test_vente_et_stop_au_prix_d_entree():
    # Vente à découvert : le cours monte au stop.
    df = bars(np.full(10, 100.0))
    df["entry"] = [True] + [False] * 9
    df["stop"], df["target"], df["exit"] = 105.0, 85.0, False
    df.loc[df.index[3], "High"] = 110.0
    (t,) = backtest.run(df, frais_bps=0, sens=-1)
    assert t.motif == "stop" and t.sortie == 105.0 and round(t.r, 6) == -1.0
    # Achat : +1 R atteint (106), puis retour à 100 : sortie au prix d'entrée, résultat nul.
    df = bars(np.full(10, 100.0))
    df["entry"] = [True] + [False] * 9
    df["stop"], df["target"], df["exit"] = 94.0, 118.0, False
    df.loc[df.index[2], "High"] = 107.0
    df.loc[df.index[3:], "Low"] = 101.0
    df.loc[df.index[4], "Low"] = 98.0
    (t,) = backtest.run(df, frais_bps=0, breakeven_r=1.0)
    assert t.motif == "stop" and t.r == 0.0 and t.sortie_date == df.index[4]


def test_filtres_du_scan():
    from tradeperso.strategies import regime_haussier
    hausse, baisse = random_walk(drift=0.002), random_walk(drift=-0.002)
    assert regime_haussier(hausse).iloc[-1] and not regime_haussier(baisse).iloc[-1]
    for seed in range(40):
        df = random_walk(seed=seed, drift=-0.0005)
        sig = scan({"^X": df, "Y": df}, {}, 10_000, 0.01, regime=regime_haussier(baisse), indices={"^X"})
        assert all(s.sens == -1 and s.symbole == "^X" for s in sig)  # marché baissier : ventes sur indices seulement
        sig = scan({"^X": df}, {}, 10_000, 0.01, regime=regime_haussier(hausse), indices={"^X"})
        assert all(s.sens == 1 for s in sig)
    df = random_walk()
    tous = scan({str(i): df for i in range(5)}, {}, 10_000, 0.01)
    assert len({s.symbole for s in tous}) == len(tous)  # un seul signal par actif
    assert scan({str(i): df for i in range(5)}, {}, 10_000, 0.01, exclus={"0"}, places=1)[:1] == [
        s for s in tous if s.symbole != "0"][:1]


def test_metrics_and_scan():
    df = random_walk()
    trades = backtest.run(STRATEGIES["rsi2_repli"].fonction(df))
    m = backtest.metrics(trades)
    assert m["trades"] == len(trades) and -100 < m["drawdown_max_pct"] <= 0
    signaux = scan({"X": df}, {"X": "Test"}, 10_000, 0.01)
    assert isinstance(to_markdown(signaux), str)
    for s in signaux:
        assert s.stop < s.entree and s.quantite > 0


def test_journal_suit_les_signaux(tmp_path):
    from tradeperso import journal
    from tradeperso.scanner import Signal

    df = random_walk(n=400, seed=3)
    d = df.index[300]
    prix = df["Close"].iloc[300]
    sig = Signal("X", "Test", "cassure_20j", d, prix, prix * 0.95, prix * 1.10, 1.0)
    assert round(sig.ratio, 6) == 2.0 and sig.type_trading == "swing"

    jrn = journal.ajouter(journal.charger(tmp_path / "j.csv"), [sig])
    jrn = journal.ajouter(jrn, [sig])  # doublon ignoré
    assert len(jrn) == 1 and jrn.loc[0, "statut"] == "en attente"

    # Le prix touche le stop deux jours après l'entrée : échec à -1 R environ.
    df.loc[df.index[301:], ["Open", "High", "Low", "Close"]] = prix
    df.loc[df.index[303], "Low"] = prix * 0.90
    clotures = journal.mettre_a_jour(jrn, {"X": df}, frais_bps=0)
    assert [c["statut"] for c in clotures] == ["échec"]
    assert jrn.loc[0, "motif"] == "stop" and round(float(jrn.loc[0, "r"]), 2) == -1.0

    journal.sauver(jrn, tmp_path / "j.csv")
    relu = journal.charger(tmp_path / "j.csv")
    b = journal.bilan(relu)
    assert (b["clos"], b["succes"], b["echecs"], b["neutres"]) == (1, 0, 1, 0)
    assert "1 échecs" in journal.to_markdown(relu)
    assert journal.statut(0.01) == "neutre"


def test_plan_execution():
    from tradeperso import execution
    from tradeperso.data import load_config
    from tradeperso.scanner import Signal

    cfg = load_config("config.toml")
    cfg["capital"]["montant"] = 10_000
    s = Signal("^NDX", "Nasdaq 100", "cassure_20j", pd.Timestamp("2026-10-02"), 30000.0, 29000.0, 32000.0, 0)
    p = execution.plan(s, cfg, execution.FX_DEFAUT)
    assert f"{p.entree_paris:%Y-%m-%d %H:%M}" == "2026-10-05 15:30"  # vendredi -> lundi, 9h30 New York
    ig, et = p.ordres
    assert ig.plateforme == "IG" and et.plateforme == "eToro"
    for o in p.ordres:
        assert 0 < o.perte_au_stop_eur <= 100.01 and o.frais_eur > 0
        assert abs(o.gain_objectif_eur / o.perte_au_stop_eur - 2.0) < 1e-6
    a = Signal("AAPL", "Apple", "rsi2_repli", pd.Timestamp("2026-10-02"), 200.0, 190.0, 215.0, 0)
    ig, et = execution.plan(a, cfg, execution.FX_DEFAUT).ordres
    assert ig.quantite == 11 and et.nuit_eur == 0 and "action réelle" in et.sous_jacent

    from tradeperso import alerts
    msgs = alerts.messages([s], [], {"succes": 0, "echecs": 0, "taux_reussite": None, "r_total": 0.0,
                                     "ouverts": 0, "en_attente": 1}, s.date, {id(s): p})
    assert len(msgs) == 2 and "lun. 5 oct. à 15h30" in msgs[0] and "30 000" in msgs[0]
    assert "Gain si l'objectif est atteint" in msgs[0] and "2,0 pour 1" in msgs[0]
    v = Signal("^GDAXI", "DAX 40", "cassure_20j_vente", pd.Timestamp("2026-10-02"), 20000.0, 20500.0, 18500.0, 0, -1)
    pv = execution.plan(v, cfg, execution.FX_DEFAUT)
    assert v.ratio == 3.0 and all(abs(o.gain_objectif_eur / o.perte_au_stop_eur - 3) < 1e-6 for o in pv.ordres)
    mv = alerts.message_signal(v, pv, 1.0)
    assert "VENTE" in mv and "Vendre" in mv and "19 500" in mv  # niveau +1 R pour remonter le stop
    assert all(x.ratio >= 3 for x in scan({"X": random_walk()}, {"X": "T"}, 10_000, 0.01, ratio_min=3))


def test_portefeuille_et_fraicheur():
    from tradeperso import portefeuille
    from tradeperso.data import fraicheur
    data = {s: random_walk(n=1500, seed=i, drift=0.0006) for i, s in enumerate(["^GSPC", "A", "B", "C", "D", "E", "F"])}
    cands = portefeuille.candidats(data, {"^GSPC"}, 5, 3.0, True, 1.0)
    assert cands
    for limite in (1, 4):
        m = portefeuille.simuler(cands, max_positions=limite)
        assert 0 < m["trades"] <= len(cands) and m["drawdown_max_pct"] <= 0
    # Jamais plus de `limite` positions ouvertes en même temps, ni deux sur le même actif.
    pris = []
    cands_tries = sorted(cands, key=lambda c: (c.trade.entree_date, c.trade.symbole, c.strategie))
    for c in cands_tries:
        ouverts = [p for p in pris if p.trade.sortie_date >= c.trade.entree_date]
        if len(ouverts) < 2 and all(p.trade.symbole != c.trade.symbole for p in ouverts):
            pris.append(c)
    assert portefeuille.simuler(cands, max_positions=2)["trades"] == len(pris)
    assert portefeuille.simuler(cands, max_positions=1)["trades"] <= len(pris)

    d = {"A": random_walk(n=50), "B": random_walk(n=40)}
    seance, perimes, retard = fraicheur(d, d["A"].index[-1] + pd.Timedelta(days=1))
    assert seance == d["A"].index[-1] and perimes == {"B"} and not retard
    assert fraicheur(d, seance + pd.Timedelta(days=10))[2]


def test_detention():
    from tradeperso import portefeuille
    idx = pd.bdate_range("2020-01-01", periods=4)
    m = portefeuille.detention(pd.Series([100.0, 80.0, 90.0, 120.0], index=idx), idx[0], idx[-1])
    assert m["rendement_total_pct"] == 20.0 and m["drawdown_max_pct"] == -20.0
    panier = pd.DataFrame({"A": [1.0, 2.0, 2.0, 2.0], "B": [1.0, 1.0, 1.0, 1.0]}, index=idx)
    assert portefeuille.detention(panier, idx[0], idx[-1])["rendement_total_pct"] == 50.0


def test_frais_trop_eleves():
    from tradeperso import alerts, execution
    from tradeperso.data import load_config
    from tradeperso.scanner import Signal
    cfg = load_config("config.toml")
    cfg["capital"]["montant"] = 3000
    s = Signal("CSCO", "Cisco", "cassure_20j", pd.Timestamp("2026-10-02"), 112.2, 106.92, 128.04, 0)
    p = execution.plan(s, cfg, execution.FX_DEFAUT)
    msg = alerts.message_signal(s, p)
    assert "Frais trop élevés" in msg and "Acheter" in msg  # IG déconseillé, eToro proposé


def test_nouvelle_introduction():
    from tradeperso.strategies import tendance_longue
    from tradeperso.indicators import sma
    df = random_walk(n=120, drift=0.004)
    t = tendance_longue(df["Close"])
    assert t.iloc[:49].isna().all() and t.iloc[-1] == sma(df["Close"], 50).iloc[-1]
    longue = random_walk(n=300)
    assert tendance_longue(longue["Close"]).iloc[-1] == sma(longue["Close"], 200).iloc[-1]


def test_speculation():
    from tradeperso import speculation
    sp = random_walk(n=400, seed=0, drift=0.0003)
    data = {f"S{i}": random_walk(n=400, seed=i + 1, drift=0.0003 * i) for i in range(8)}
    t = speculation.classement(data, {}, sp)
    assert list(t["rang"]) == list(range(1, 9)) and t["force_relative_pct"].is_monotonic_decreasing
    choix = speculation.selection(t, [], 3)
    assert len(choix) <= 3 and all(t.set_index("symbole").loc[s, "cours"] > t.set_index("symbole").loc[s, "moyenne_50j"] for s in choix)
    # Une action détenue encore dans le top 6 et au-dessus de sa MM50 est gardée.
    ok = t[t["cours"] > t["moyenne_50j"]]
    if len(ok) >= 4:
        garde = ok["symbole"].iloc[3]
        assert garde in speculation.selection(t, [garde], 3)
    courbe = speculation.rotation(data, sp, 3, 126)
    assert len(courbe) == 400 and courbe.iloc[0] == 1.0 and (courbe > 0).all()


def test_daytrading():
    from tradeperso import daytrading
    n = daytrading.niveaux(110, 100, 10)
    assert (n.achat, n.achat_ko, n.achat_objectif) == (111, 106, 126) and (n.vente, n.vente_ko, n.vente_objectif) == (99, 104, 84)
    idx = pd.bdate_range("2020-01-01", periods=30)
    df = pd.DataFrame({"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0}, index=idx)
    # Dernier jour : cassure du plus haut puis montée jusqu'à l'objectif (+3 R hors frais).
    df.iloc[-1] = [100.5, 110.0, 100.4, 109.0]
    rs = daytrading.backtest(df, frais_bps=0)
    assert round(rs[-1], 6) == 3.0
    # Cassure puis retour sous le knock-out : -1 R.
    df.iloc[-1] = [100.5, 101.5, 99.5, 100.0]
    assert round(daytrading.backtest(df, frais_bps=0)[-1], 6) == -1.0
