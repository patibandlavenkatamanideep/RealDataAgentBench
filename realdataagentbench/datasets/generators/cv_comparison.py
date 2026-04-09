"""CV comparison dataset — noisy binary classification for k-fold vs hold-out comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Small dataset — variance of single hold-out is high, k-fold is more stable
    feature_1 = rng.normal(0, 1, n_rows)
    feature_2 = rng.normal(0, 1, n_rows)
    feature_3 = rng.normal(0, 1, n_rows)
    feature_4 = rng.uniform(-2, 2, n_rows)
    feature_5 = rng.normal(1, 2, n_rows)

    # Noisy signal
    log_odds = 0.8 * feature_1 - 0.5 * feature_2 + 0.3 * feature_4 + rng.normal(0, 1.2, n_rows)
    prob = 1 / (1 + np.exp(-log_odds))
    target = (rng.uniform(0, 1, n_rows) < prob).astype(int)

    return pd.DataFrame({
        "feature_1": np.round(feature_1, 4),
        "feature_2": np.round(feature_2, 4),
        "feature_3": np.round(feature_3, 4),
        "feature_4": np.round(feature_4, 4),
        "feature_5": np.round(feature_5, 4),
        "target": target,
    })
