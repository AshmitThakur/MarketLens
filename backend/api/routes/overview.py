"""Health, overview, and state-summary endpoints."""

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_data_service
from backend.api.models import HealthResponse, OverviewResponse, StateSummary
from backend.services.data_service import DataService


router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="MarketLens API")


@router.get("/overview", response_model=OverviewResponse)
def overview(service: DataService = Depends(get_data_service)) -> dict:
    cities = service.cities
    metadata = service.metadata
    top = cities.iloc[0]
    current_period = metadata["growth_windows"]["current"]
    return {
        "total_stores": metadata["total_stores"],
        "cities_analyzed": len(cities),
        "states": metadata["number_of_states"],
        "product_families": metadata["number_of_product_families"],
        "top_opportunity": {
            "city": top["city"],
            "state": top["state"],
            "score": top["opportunity_score"],
        },
        "analysis_period": {"start": current_period[0], "end": current_period[1]},
    }


@router.get("/states", response_model=list[StateSummary])
def states(service: DataService = Depends(get_data_service)) -> list[dict]:
    return service.state_summaries()
