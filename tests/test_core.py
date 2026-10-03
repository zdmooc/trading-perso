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
