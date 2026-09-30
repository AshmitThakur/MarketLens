"""City listing and detail endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.dependencies import get_data_service
from backend.api.models import CityDetail, CityMetrics
from backend.services.data_service import DataService


router = APIRouter(prefix="/api/cities", tags=["cities"])


@router.get("", response_model=list[CityMetrics])
def cities(
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    state: Annotated[str | None, Query(min_length=1)] = None,
    service: DataService = Depends(get_data_service),
) -> list[dict]:
    return service.list_cities(state=state, limit=limit)


@router.get("/{city}", response_model=CityDetail)
def city_detail(
    city: str, service: DataService = Depends(get_data_service)
) -> dict:
    result = service.find_city(city)
    if result is None:
        raise HTTPException(status_code=404, detail=f"City '{city}' was not found")
    return {**result, "weights": service.default_weight_response()}
