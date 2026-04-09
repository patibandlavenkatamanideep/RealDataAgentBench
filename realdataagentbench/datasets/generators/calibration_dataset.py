"""Calibration dataset — classifier outputs uncalibrated probabilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    age = rng.integers(18, 75, n_rows)
    bmi = rng.normal(27, 6, n_rows).clip(16, 50)
    systolic_bp = rng.normal(125, 20, n_rows).clip(80, 200)
    cholesterol = rng.normal(200, 40, n_rows).clip(100, 350)
    smoking = rng.choice([0, 1], n_rows, p=[0.75, 0.25])
    family_history = rng.choice([0, 1], n_rows, p=[0.70, 0.30])
    exercise_days = rng.integers(0, 7, n_rows)

    log_odds = (
        -5.0
        + 0.04 * age
        + 0.06 * bmi
        + 0.02 * (systolic_bp - 120)
        + 0.008 * (cholesterol - 200)
        + 0.7 * smoking
        + 0.5 * family_history
        - 0.1 * exercise_days
        + rng.normal(0, 0.5, n_rows)
    )
    true_prob = 1 / (1 + np.exp(-log_odds))
    heart_disease = (rng.uniform(0, 1, n_rows) < true_prob).astype(int)

    return pd.DataFrame({
        "age": age,
        "bmi": np.round(bmi, 2),
        "systolic_bp": np.round(systolic_bp, 1),
        "cholesterol": np.round(cholesterol, 1),
        "smoking": smoking,
        "family_history": family_history,
        "exercise_days": exercise_days,
        "heart_disease": heart_disease,
    })
