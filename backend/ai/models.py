"""Validated request and structured-response models for MarketLens AI."""

from pydantic import BaseModel, Field, field_validator, model_validator


class KeyFinding(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    explanation: str = Field(min_length=1, max_length=700)


class ExecutiveInsightsResponse(BaseModel):
    executive_summary: str = Field(min_length=1, max_length=1200)
    key_findings: list[KeyFinding] = Field(min_length=1, max_length=6)
    opportunities: list[str] = Field(min_length=1, max_length=6)
    risks_and_caveats: list[str] = Field(min_length=1, max_length=8)
    recommended_next_steps: list[str] = Field(min_length=1, max_length=6)


class CityComparisonRequest(BaseModel):
    city_a: str = Field(min_length=1, max_length=100)
    city_b: str = Field(min_length=1, max_length=100)

    @field_validator("city_a", "city_b")
    @classmethod
    def strip_city_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("city name cannot be empty")
        return value

    @model_validator(mode="after")
    def cities_must_differ(self) -> "CityComparisonRequest":
        if self.city_a.casefold() == self.city_b.casefold():
            raise ValueError("select two different cities")
        return self


class CityComparisonResponse(BaseModel):
    city_a: str
    city_b: str
    summary: str = Field(min_length=1, max_length=1200)
    advantages_city_a: list[str] = Field(min_length=1, max_length=6)
    advantages_city_b: list[str] = Field(min_length=1, max_length=6)
    main_tradeoffs: list[str] = Field(min_length=1, max_length=6)
    management_interpretation: str = Field(min_length=1, max_length=1000)


class AskMarketLensRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question cannot be empty")
        return value


class AskMarketLensResponse(BaseModel):
    answer: str = Field(min_length=1, max_length=1800)
    supporting_points: list[str] = Field(default_factory=list, max_length=8)
    cities_referenced: list[str] = Field(default_factory=list, max_length=22)
    caveat: str | None = Field(default=None, max_length=800)
