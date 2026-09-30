"""Grounded MarketLens AI endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from backend.ai.gemini_service import (
    AIConfigurationError,
    AIResponseError,
    AIServiceError,
    GeminiService,
)
from backend.ai.models import (
    AskMarketLensRequest,
    AskMarketLensResponse,
    CityComparisonRequest,
    CityComparisonResponse,
    ExecutiveInsightsResponse,
)
from backend.api.dependencies import get_ai_service, get_data_service
from backend.services.data_service import DataService


router = APIRouter(prefix="/api/ai", tags=["AI copilot"])

LIMITATIONS = [
    "No profitability or price data",
    "No real-estate costs",
    "No population or demographic data",
    "No competitor information",
    "No logistics costs",
    "No market-size information",
]

METHODOLOGY = {
    "activity_period": "2016-08-16 through 2017-08-15",
    "growth_comparison_period": "2015-08-17 through 2016-08-15",
    "normalization": "Each component is a 0-100 percentile score across cities",
    "purpose": "Decision support and investigation prioritization, not prediction",
}


def _weights(service: DataService) -> dict[str, float]:
    return service.default_weight_response()


def _handle_ai_error(error: Exception) -> None:
    if isinstance(error, AIConfigurationError):
        raise HTTPException(status_code=503, detail=str(error)) from error
    if isinstance(error, (AIServiceError, AIResponseError)):
        raise HTTPException(status_code=502, detail=str(error)) from error
    raise error


@router.post("/insights", response_model=ExecutiveInsightsResponse)
def executive_insights(
    data: DataService = Depends(get_data_service),
    ai: GeminiService = Depends(get_ai_service),
) -> ExecutiveInsightsResponse:
    fields = [
        "city",
        "state",
        "opportunity_score",
        "sales_score",
        "transaction_score",
        "growth_score",
        "breadth_score",
        "active_stores",
    ]
    context = {
        "top_five_cities": data.cities.head(5)[fields].to_dict(orient="records"),
        "current_weights": _weights(data),
        "methodology": METHODOLOGY,
        "limitations": LIMITATIONS,
    }
    try:
        return ai.executive_insights(context)
    except (AIConfigurationError, AIServiceError, AIResponseError) as error:
        _handle_ai_error(error)


@router.post("/compare", response_model=CityComparisonResponse)
def compare_cities(
    request: CityComparisonRequest,
    data: DataService = Depends(get_data_service),
    ai: GeminiService = Depends(get_ai_service),
) -> CityComparisonResponse:
    city_a = data.find_city(request.city_a)
    city_b = data.find_city(request.city_b)
    if city_a is None:
        raise HTTPException(status_code=404, detail=f"City '{request.city_a}' was not found")
    if city_b is None:
        raise HTTPException(status_code=404, detail=f"City '{request.city_b}' was not found")

    context = {
        "city_a": city_a,
        "city_b": city_b,
        "current_weights": _weights(data),
        "methodology": METHODOLOGY,
        "limitations": LIMITATIONS,
    }
    try:
        result = ai.compare_cities(context)
        return result.model_copy(update={"city_a": city_a["city"], "city_b": city_b["city"]})
    except (AIConfigurationError, AIServiceError, AIResponseError) as error:
        _handle_ai_error(error)


@router.post("/ask", response_model=AskMarketLensResponse)
def ask_marketlens(
    request: AskMarketLensRequest,
    data: DataService = Depends(get_data_service),
    ai: GeminiService = Depends(get_ai_service),
) -> AskMarketLensResponse:
    context = {
        "cities": data.cities.to_dict(orient="records"),
        "current_weights": _weights(data),
        "methodology": METHODOLOGY,
        "limitations": LIMITATIONS,
    }
    try:
        result = ai.ask(request.question, context)
        valid_names = {
            city_name.casefold(): city_name for city_name in data.cities["city"].tolist()
        }
        grounded_references = list(
            dict.fromkeys(
                valid_names[name.casefold()]
                for name in result.cities_referenced
                if name.casefold() in valid_names
            )
        )
        return result.model_copy(update={"cities_referenced": grounded_references})
    except (AIConfigurationError, AIServiceError, AIResponseError) as error:
        _handle_ai_error(error)
