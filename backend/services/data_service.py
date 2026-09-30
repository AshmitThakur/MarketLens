"""Cached access to processed MarketLens analytics data."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from backend.analytics.scoring import DEFAULT_WEIGHTS, METRIC_COLUMNS, validate_weights


CITY_COLUMNS = [
    "city",
    "state",
    "active_stores",
    "total_sales",
    "sales_per_store",
    "total_transactions",
    "transactions_per_store",
    "comparable_growth_pct",
    "category_breadth",
    "sales_score",
    "transaction_score",
    "growth_score",
    "breadth_score",
    "opportunity_score",
]


class DataService:
    """Load processed analytics once and serve inexpensive in-memory queries."""

    def __init__(
        self,
        metrics_path: str | Path,
        metadata_path: str | Path,
    ) -> None:
        self.metrics_path = Path(metrics_path)
        self.metadata_path = Path(metadata_path)
        self._cities: pd.DataFrame | None = None
        self._metadata: dict[str, Any] | None = None

    def load(self) -> None:
        """Load and validate the processed artifacts into memory."""
        if not self.metrics_path.is_file():
            raise FileNotFoundError(
                f"Processed city metrics not found: {self.metrics_path}. "
                "Run python -m backend.analytics.pipeline first."
            )
        if not self.metadata_path.is_file():
            raise FileNotFoundError(
                f"Analysis metadata not found: {self.metadata_path}. "
                "Run python -m backend.analytics.pipeline first."
            )

        cities = pd.read_csv(self.metrics_path)
        missing_columns = sorted(set(CITY_COLUMNS) - set(cities.columns))
        if missing_columns:
            raise ValueError(f"city_metrics.csv is missing columns: {missing_columns}")
        if cities[CITY_COLUMNS].isna().any().any():
            raise ValueError("city_metrics.csv contains missing values")
        if cities.duplicated(["city", "state"]).any():
            raise ValueError("city_metrics.csv contains duplicate city/state rows")

        self._cities = cities[CITY_COLUMNS].sort_values(
            "opportunity_score", ascending=False
        ).reset_index(drop=True)
        self._metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))

    @property
    def cities(self) -> pd.DataFrame:
        if self._cities is None:
            self.load()
        return self._cities.copy()  # type: ignore[union-attr]

    @property
    def metadata(self) -> dict[str, Any]:
        if self._metadata is None:
            self.load()
        return dict(self._metadata)  # type: ignore[arg-type]

    def list_cities(self, state: str | None = None, limit: int | None = None) -> list[dict]:
        """Return ranked cities with optional case-insensitive state filtering."""
        cities = self.cities
        if state:
            cities = cities.loc[cities["state"].str.casefold() == state.casefold()]
        if limit is not None:
            cities = cities.head(limit)
        return cities.to_dict(orient="records")

    def find_city(self, city: str) -> dict | None:
        """Find a city by case-insensitive exact name."""
        matches = self.cities.loc[self.cities["city"].str.casefold() == city.casefold()]
        if matches.empty:
            return None
        return matches.iloc[0].to_dict()

    def rescore(self, weights: dict[str, float]) -> list[dict]:
        """Re-rank cached component scores without rerunning raw analytics."""
        weights = validate_weights(weights)
        cities = self.cities
        cities["opportunity_score"] = sum(
            cities[score_column] * weights[key]
            for key, (_, score_column) in METRIC_COLUMNS.items()
        )
        cities = cities.sort_values("opportunity_score", ascending=False).reset_index(
            drop=True
        )
        return cities.to_dict(orient="records")

    def state_summaries(self) -> list[dict]:
        """Aggregate simple state-level filtering statistics."""
        summaries = (
            self.cities.groupby("state", as_index=False)
            .agg(
                cities=("city", "nunique"),
                stores=("active_stores", "sum"),
                average_opportunity_score=("opportunity_score", "mean"),
            )
            .sort_values("average_opportunity_score", ascending=False)
        )
        return summaries.to_dict(orient="records")

    @staticmethod
    def default_weight_response() -> dict[str, float]:
        return {
            "sales_weight": DEFAULT_WEIGHTS["sales"],
            "transaction_weight": DEFAULT_WEIGHTS["transactions"],
            "growth_weight": DEFAULT_WEIGHTS["growth"],
            "breadth_weight": DEFAULT_WEIGHTS["breadth"],
        }
