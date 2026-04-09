"""E-commerce transactions generator — Simpson's Paradox setup."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 2000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Three segments with very different baseline revenues
    # Enterprise: large orders, large revenue, but also large discounts (procurement)
    # SMB: medium orders, medium revenue, small discounts
    # Consumer: small orders, low revenue, tiny discounts
    segments = rng.choice(
        ["enterprise", "smb", "consumer"],
        size=n_rows,
        p=[0.20, 0.35, 0.45],
    )

    discount_pct = np.zeros(n_rows)
    order_size = np.zeros(n_rows)
    revenue = np.zeros(n_rows)

    for i, seg in enumerate(segments):
        if seg == "enterprise":
            d = rng.uniform(0.15, 0.35)
            o = rng.normal(50_000, 10_000)
            r = o * (1 - d * 0.3) + rng.normal(0, 500)
        elif seg == "smb":
            d = rng.uniform(0.05, 0.15)
            o = rng.normal(8_000, 2_000)
            r = o * (1 - d * 0.2) + rng.normal(0, 200)
        else:  # consumer
            d = rng.uniform(0.0, 0.05)
            o = rng.normal(200, 80)
            r = o * (1 - d * 0.1) + rng.normal(0, 10)

        discount_pct[i] = max(0.0, d)
        order_size[i] = max(10.0, o)
        revenue[i] = max(1.0, r)

    # Raw correlation: enterprise has high discounts + high revenue → marginal positive
    # But overall, high-discount consumers have low revenue → raw is negative
    # Partial (controlling order_size) collapses toward zero

    return pd.DataFrame({
        "transaction_id": np.arange(1, n_rows + 1),
        "customer_segment": segments,
        "order_size": np.round(order_size, 2),
        "discount_pct": np.round(discount_pct, 4),
        "revenue": np.round(revenue, 2),
    })
