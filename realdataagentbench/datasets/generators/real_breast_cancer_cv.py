"""Breast Cancer Wisconsin — cross-validation and model evaluation dataset.

Same source as real_breast_cancer.py but used for an ML engineering task
focused on comparing k-fold CV vs hold-out evaluation.

Source: UCI Machine Learning Repository / sklearn.datasets.load_breast_cancer()
License: BSD 3-Clause (sklearn) / Public domain (UCI)
Samples: 569 | Features: 30 | Task: Binary classification evaluation design
"""

from __future__ import annotations

import pandas as pd
from sklearn.datasets import load_breast_cancer


def generate(n_rows: int = 569, seed: int = 42) -> pd.DataFrame:
    """Return the Breast Cancer Wisconsin dataset for CV evaluation tasks.

    Target column: `diagnosis` — 0 = malignant (212), 1 = benign (357).
    This loader is identical to real_breast_cancer but registered separately
    so different tasks can reference different generator names in their YAMLs.
    """
    bc = load_breast_cancer()
    df = pd.DataFrame(bc.data, columns=bc.feature_names)
    df["diagnosis"] = bc.target
    return df
