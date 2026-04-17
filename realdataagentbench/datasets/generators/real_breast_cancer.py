"""Breast Cancer Wisconsin (Diagnostic) — real dataset loader.

Source: UCI Machine Learning Repository / sklearn.datasets.load_breast_cancer()
License: BSD 3-Clause (sklearn) / Public domain (UCI)
Samples: 569 | Features: 30 | Task: Binary classification (malignant vs benign)

The `seed` and `n_rows` params are accepted for API compatibility but ignored —
this is fixed real-world data, not a synthetic generator.
"""

from __future__ import annotations

import pandas as pd
from sklearn.datasets import load_breast_cancer


def generate(n_rows: int = 569, seed: int = 42) -> pd.DataFrame:
    """Return the Breast Cancer Wisconsin dataset as a DataFrame.

    Target column: `diagnosis` — 0 = malignant (212 samples), 1 = benign (357 samples).
    All 30 features are real-valued measurements computed from digitized images
    of fine needle aspirates (FNA) of breast masses.
    """
    bc = load_breast_cancer()
    df = pd.DataFrame(bc.data, columns=bc.feature_names)
    df["diagnosis"] = bc.target  # 0=malignant, 1=benign
    return df
