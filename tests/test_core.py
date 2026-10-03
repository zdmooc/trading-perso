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
    for name, strat in STRATEGIES.items():
        out = strat(df)
        assert {"entry", "stop", "target", "exit"} <= set(out.columns), name
        trades = backtest.run(out, "TEST")
        assert trades, f"{name} n'a produit aucun trade"
        for t in trades:
            assert t.sortie_date > t.entree_date or t.motif in {"stop", "objectif"}
            assert t.stop < t.entree


def test_stop_hit_gives_about_minus_one_r():
    df = bars(np.full(10, 100.0))
    df["entry"] = [True] + [False] * 9
    df["stop"], df["target"], df["exit"] = 95.0, np.nan, False
    df.loc[df.index[3], "Low"] = 90.0
    (t,) = backtest.run(df, frais_bps=0)
    assert t.motif == "stop" and t.sortie == 95.0 and round(t.r, 6) == -1.0


def test_metrics_and_scan():
    df = random_walk()
    trades = backtest.run(STRATEGIES["rsi2_repli"](df))
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
    assert (b["clos"], b["succes"], b["echecs"]) == (1, 0, 1)
    assert "1 échecs" in journal.to_markdown(relu)


def test_plan_execution():
    from tradeperso import execution
    from tradeperso.data import load_config
    from tradeperso.scanner import Signal

    cfg = load_config("config.toml")
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
    assert all(x.ratio >= 3 for x in scan({"X": random_walk()}, {"X": "T"}, 10_000, 0.01, ratio_min=3))
