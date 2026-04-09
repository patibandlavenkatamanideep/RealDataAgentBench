"""Leakage dataset — classification with a target-leaking feature injected."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 600, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    age = rng.integers(20, 70, n_rows)
    income = rng.normal(55000, 20000, n_rows).clip(15000, 200000)
    credit_score = rng.integers(300, 850, n_rows)
    debt_ratio = rng.uniform(0.05, 0.6, n_rows)
    employment_years = rng.integers(0, 35, n_rows)
    num_accounts = rng.integers(1, 12, n_rows)

    # True label
    log_odds = (
        -3.0
        + 0.03 * (credit_score - 600) / 100
        + 0.02 * employment_years
        - 1.5 * debt_ratio
        + rng.normal(0, 0.4, n_rows)
    )
    prob = 1 / (1 + np.exp(-log_odds))
    approved = (rng.uniform(0, 1, n_rows) < prob).astype(int)

    # LEAKING FEATURE: derived directly from the label with tiny noise
    # An agent that scales/encodes before splitting will use this in training
    approval_code = approved * 100 + rng.integers(0, 5, n_rows)  # 0-4 vs 100-104

    return pd.DataFrame({
        "age": age,
        "income": np.round(income, 2),
        "credit_score": credit_score,
        "debt_ratio": np.round(debt_ratio, 4),
        "employment_years": employment_years,
        "num_accounts": num_accounts,
        "approval_code": approval_code,   # <-- leaking feature
        "approved": approved,
    })
