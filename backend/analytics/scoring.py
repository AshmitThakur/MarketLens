"""Normalize city metrics and calculate the weighted opportunity score."""

from collections.abc import Mapping

import numpy as np
import pandas as pd


DEFAULT_WEIGHTS = {
    "sales": 0.40,
    "transactions": 0.30,
    "growth": 0.20,
    "breadth": 0.10,
}

METRIC_COLUMNS = {
    "sales": ("sales_per_store", "sales_score"),
    "transactions": ("transactions_per_store", "transaction_score"),
    "growth": ("comparable_growth_pct", "growth_score"),
    "breadth": ("category_breadth", "breadth_score"),
}


def validate_weights(weights: Mapping[str, float]) -> dict[str, float]:
    """Require the four expected, non-negative weights to total one."""
    expected = set(METRIC_COLUMNS)
    supplied = set(weights)
    if supplied != expected:
        raise ValueError(
            f"weights must contain exactly {sorted(expected)}; received {sorted(supplied)}"
        )
    clean = {key: float(value) for key, value in weights.items()}
    if any(value < 0 for value in clean.values()):
        raise ValueError("weights cannot be negative")
    if not np.isclose(sum(clean.values()), 1.0):
        raise ValueError("weights must sum to 1.0")
    return clean


def percentile_score(values: pd.Series) -> pd.Series:
    """Convert values to 0-100 percentile ranks while preserving missing values."""
    valid = values.dropna()
    if valid.empty:
        return pd.Series(np.nan, index=values.index, dtype=float)
    if valid.nunique() == 1:
        scores = pd.Series(50.0, index=valid.index)
    else:
        ranks = valid.rank(method="average")
        # Normalize observed ranks so tied minima/maxima still map to 0/100.
        scores = (ranks - ranks.min()) / (ranks.max() - ranks.min()) * 100
    return scores.reindex(values.index)


def score_city_metrics(
    metrics: pd.DataFrame, weights: Mapping[str, float] | None = None
) -> pd.DataFrame:
    """Add percentile component scores and the configured weighted score."""
    weights = validate_weights(DEFAULT_WEIGHTS if weights is None else weights)
    result = metrics.copy()

    for raw_column, score_column in METRIC_COLUMNS.values():
        result[score_column] = percentile_score(result[raw_column])

    # Multiplication is intentionally explicit: any missing component leaves the
    # composite missing instead of silently reallocating its weight.
    result["opportunity_score"] = sum(
        result[score_column] * weights[key]
        for key, (_, score_column) in METRIC_COLUMNS.items()
    )
    return result.sort_values(
        "opportunity_score", ascending=False, na_position="last"
    ).reset_index(drop=True)
