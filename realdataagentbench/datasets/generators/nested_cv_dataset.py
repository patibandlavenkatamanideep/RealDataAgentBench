"""Nested CV dataset — regression with hyperparameter tuning for unbiased evaluation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 400, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # 10 features, 4 informative, 6 noise
    x1 = rng.normal(0, 1, n_rows)
    x2 = rng.normal(2, 1.5, n_rows)
    x3 = rng.uniform(-3, 3, n_rows)
    x4 = rng.normal(0, 2, n_rows)
    noise = rng.normal(0, 1, (n_rows, 6))

    target = (
        3.5 * x1
        - 2.0 * x2
        + 1.5 * x3 ** 2   # nonlinear
        + 0.8 * x4
        + rng.normal(0, 2, n_rows)
    )

    df = pd.DataFrame({
        "x1": np.round(x1, 4),
        "x2": np.round(x2, 4),
        "x3": np.round(x3, 4),
        "x4": np.round(x4, 4),
    })
    for i in range(6):
        df[f"noise_{i+1}"] = np.round(noise[:, i], 4)
    df["target"] = np.round(target, 4)
    return df
