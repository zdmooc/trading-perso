"""Copie temporaire des cours Yahoo (horaire et journalier) pour les tests d'amélioration des signaux."""
from __future__ import annotations

import gzip
import pickle
from pathlib import Path

from tradeperso import matin, plan
from tradeperso.data import download, load_config, watchlist

h = matin.telecharger(plan.INDICES, "730d", "1h")
d = matin.telecharger(plan.INDICES, "5y", "1d")
noms = watchlist(load_config())
j = download(sorted(set(noms) | {"^GSPC"}), period="10y")
Path("reports/tmp").mkdir(parents=True, exist_ok=True)
with gzip.open("reports/tmp/donnees.pkl.gz", "wb") as f:
    pickle.dump({"h": h, "d": d, "j": j, "noms": noms}, f)
print({s: (str(x.index[0]), len(x)) for s, x in h.items()}, len(j))
