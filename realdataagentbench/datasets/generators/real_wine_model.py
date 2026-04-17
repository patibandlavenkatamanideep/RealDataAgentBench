"""Wine Recognition dataset — modeling variant.

Same source as real_wine.py but registered separately for use in modeling
tasks that require multi-class classification with model comparison.

Source: Forina et al. (1986), UCI ML Repository / sklearn.datasets.load_wine()
License: BSD 3-Clause (sklearn) / Public domain (UCI)
Samples: 178 | Features: 13 | Task: Multi-class classification modeling
"""

from __future__ import annotations

import pandas as pd
from sklearn.datasets import load_wine


def generate(n_rows: int = 178, seed: int = 42) -> pd.DataFrame:
    """Return the Wine Recognition dataset for modeling tasks.

    13 chemical measurements (alcohol, malic_acid, ash, alcalinity_of_ash,
    magnesium, total_phenols, flavanoids, nonflavanoid_phenols, proanthocyanins,
    color_intensity, hue, od280/od315_of_diluted_wines, proline).

    Target column: `wine_class` — 0, 1, or 2.
    Class distribution: class_0=59, class_1=71, class_2=48.
    """
    wine = load_wine()
    df = pd.DataFrame(wine.data, columns=wine.feature_names)
    df["wine_class"] = wine.target
    return df
