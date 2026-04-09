"""Ensemble dataset — multi-class classification for stacking/voting comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 700, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # 8 numeric features with mixed signal
    X = rng.normal(0, 1, (n_rows, 8))
    feature_names = [f"feature_{i+1}" for i in range(8)]

    # 3-class target: class boundaries are nonlinear
    scores = np.column_stack([
        2.0 * X[:, 0] - 1.5 * X[:, 1] + rng.normal(0, 0.8, n_rows),
        1.5 * X[:, 2] + 1.0 * X[:, 3] - 0.5 * X[:, 0] + rng.normal(0, 0.8, n_rows),
        -1.0 * X[:, 4] + 2.0 * X[:, 5] + rng.normal(0, 0.8, n_rows),
    ])
    target = np.argmax(scores, axis=1)  # 0, 1, or 2

    df = pd.DataFrame(np.round(X, 4), columns=feature_names)
    df["target"] = target
    return df
