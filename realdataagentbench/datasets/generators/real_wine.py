"""Wine Recognition dataset — real dataset loader.

Source: Forina et al. (1986), UCI ML Repository / sklearn.datasets.load_wine()
License: BSD 3-Clause (sklearn) / Public domain (UCI)
Samples: 178 | Features: 13 | Task: 3-class classification (wine cultivar)

The `seed` and `n_rows` params are accepted for API compatibility but ignored.
"""

from __future__ import annotations

import pandas as pd
from sklearn.datasets import load_wine


def generate(n_rows: int = 178, seed: int = 42) -> pd.DataFrame:
    """Return the Wine Recognition dataset as a DataFrame.

    13 chemical measurements from wines grown in the same region of Italy
    by three different cultivars.

    Target column: `wine_class` — 0, 1, or 2 (three cultivars).
    Class distribution: class_0=59, class_1=71, class_2=48.
    """
    wine = load_wine()
    df = pd.DataFrame(wine.data, columns=wine.feature_names)
    df["wine_class"] = wine.target
    return df
