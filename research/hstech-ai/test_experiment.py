"""Tests hors marché pour valider la mécanique, non des performances de trading."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SPEC = importlib.util.spec_from_file_location("hstech_experiment", Path(__file__).with_name("experiment.py"))
exp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exp)


def fixture_prices(n=520):
    rng = np.random.default_rng(87)
    previous = 3500.0
    bars = []
    for day in pd.bdate_range("2023-01-02", periods=n):
        open_ = previous * (1 + rng.normal(0, 0.007))
        close = open_ * (1 + rng.normal(0, 0.018))
        high = max(open_, close) * (1 + abs(rng.normal(0, 0.003)))
        low = min(open_, close) * (1 - abs(rng.normal(0, 0.003)))
        bars.append((day, open_, high, low, close))
        previous = close
    return pd.DataFrame(bars, columns=["Date", "Open", "High", "Low", "Close"])


def test_features_use_close_j_and_label_j_plus_1():
    raw = fixture_prices(350).set_index("Date")
    ds = exp.prepare(raw)
    day = ds.index[50]
    i = raw.index.get_loc(day)
    expected = raw["Close"].iloc[i + 1] / raw["Open"].iloc[i + 1] - 1
    assert ds.loc[day, "next_intraday_return"] == pytest.approx(expected)
    changed = raw.copy()
    changed.loc[raw.index[i + 1], "Close"] *= 1.01
    ds_changed = exp.prepare(changed)
    for feat in exp.FEATURES:
        assert ds_changed.loc[day, feat] == pytest.approx(ds.loc[day, feat])
    assert ds_changed.loc[day, "next_intraday_return"] != ds.loc[day, "next_intraday_return"]


def test_temporal_splits_purge_boundary():
    ds = exp.prepare(fixture_prices(520).set_index("Date"))
    tr, va, te = exp.chronological_blocks(ds)
    all_index = ds.index
    assert all_index.get_loc(va.index[0]) - all_index.get_loc(tr.index[-1]) == 2
    assert all_index.get_loc(te.index[0]) - all_index.get_loc(va.index[-1]) == 2
    assert tr.index.max() < va.index.min() < te.index.min()


def test_reject_bad_ohlc_and_short_history(tmp_path):
    fixture_prices(350).assign(High=0).to_csv(tmp_path / "bad.csv", index=False)
    with pytest.raises(ValueError, match="Prix"):
        exp.load_ohlc(tmp_path / "bad.csv")
    short = exp.prepare(fixture_prices(90).set_index("Date"))
    with pytest.raises(ValueError, match="300"):
        exp.chronological_blocks(short)


def test_end_to_end_synthetic_pipeline(tmp_path):
    path = tmp_path / "synthetic.csv"
    fixture_prices().to_csv(path, index=False)
    report = exp.evaluate(path)
    assert report["symbol"] == "HSTECH.HK"
    assert report["champion"] in report["validation"]
    assert report["status"] == "RESEARCH_ONLY_NOT_TRADING_AUTHORIZED"
    assert report["splits"]["train"]["last"] < report["splits"]["validation"]["first"]
    assert report["test_once_out_of_sample"]["days"] > 40
