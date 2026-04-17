"""Diabetes dataset — real dataset loader.

Source: Efron et al. (2004) / sklearn.datasets.load_diabetes()
License: BSD 3-Clause (sklearn) | DOI: 10.1214/009053604000000067
Samples: 442 | Features: 10 | Task: Regression (disease progression at 1 year)

All feature values are mean-centered and scaled by the standard deviation
times the square root of n_samples (i.e., the sum of squares of each column
totals 1). The `seed` and `n_rows` params are accepted for API compatibility
but ignored.
"""

from __future__ import annotations

import pandas as pd
from sklearn.datasets import load_diabetes


def generate(n_rows: int = 442, seed: int = 42) -> pd.DataFrame:
    """Return the diabetes dataset as a DataFrame.

    Features: age, sex, bmi, bp, s1 (tc), s2 (ldl), s3 (hdl), s4 (tch), s5 (ltg), s6 (glu)
    Target column: `disease_progression` — quantitative measure of disease progression one year
    after baseline (range: 25–346, mean ≈ 152.1).
    """
    diab = load_diabetes()
    df = pd.DataFrame(diab.data, columns=diab.feature_names)
    df["disease_progression"] = diab.target
    return df
