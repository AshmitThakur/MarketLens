"""Pydantic request and response models for the MarketLens API."""

import math

from pydantic import BaseModel, Field, model_validator


class HealthResponse(BaseModel):
    status: str
    service: str


class AnalysisPeriod(BaseModel):
    start: str
    end: str


class TopOpportunity(BaseModel):
    city: str
    state: str
    score: float


class OverviewResponse(BaseModel):
    total_stores: int
    cities_analyzed: int
    states: int
    product_families: int
    top_opportunity: TopOpportunity
    analysis_period: AnalysisPeriod


class WeightConfiguration(BaseModel):
    sales_weight: float
    transaction_weight: float
    growth_weight: float
    breadth_weight: float


class ScoringRequest(BaseModel):
    sales_weight: float = Field(ge=0)
    transaction_weight: float = Field(ge=0)
    growth_weight: float = Field(ge=0)
    breadth_weight: float = Field(ge=0)

    @model_validator(mode="after")
    def weights_must_sum_to_one(self) -> "ScoringRequest":
        total = (
            self.sales_weight
            + self.transaction_weight
            + self.growth_weight
            + self.breadth_weight
        )
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError("weights must sum to 1.0")
        return self

    def as_score_mapping(self) -> dict[str, float]:
        """Map API field names to the existing analytics score names."""
        return {
            "sales": self.sales_weight,
            "transactions": self.transaction_weight,
            "growth": self.growth_weight,
            "breadth": self.breadth_weight,
        }


class CityMetrics(BaseModel):
    city: str
    state: str
    active_stores: int
    total_sales: float
    sales_per_store: float
    total_transactions: float
    transactions_per_store: float
    comparable_growth_pct: float
    category_breadth: int
    sales_score: float
    transaction_score: float
    growth_score: float
    breadth_score: float
    opportunity_score: float


class CityDetail(CityMetrics):
    weights: WeightConfiguration


class StateSummary(BaseModel):
    state: str
    cities: int
    stores: int
    average_opportunity_score: float
