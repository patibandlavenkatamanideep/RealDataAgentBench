"""Iris dataset — real dataset loader.

Source: Fisher (1936) / sklearn.datasets.load_iris()
License: BSD 3-Clause (sklearn) / Public domain
Samples: 150 | Features: 4 | Task: 3-class classification (iris species)

The `seed` and `n_rows` params are accepted for API compatibility but ignored.
"""

from __future__ import annotations

import pandas as pd
from sklearn.datasets import load_iris


def generate(n_rows: int = 150, seed: int = 42) -> pd.DataFrame:
    """Return the Iris dataset as a DataFrame.

    4 features: sepal length (cm), sepal width (cm), petal length (cm), petal width (cm)
    Target column: `species` — 0=setosa, 1=versicolor, 2=virginica (50 samples each).

    Setosa is linearly separable from the other two classes.
    Petal length and petal width are the most discriminating features.
    """
    iris = load_iris()
    df = pd.DataFrame(iris.data, columns=iris.feature_names)
    df["species"] = iris.target
    return df
