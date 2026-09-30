"""Custom score recalculation endpoint."""

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_data_service
from backend.api.models import CityMetrics, ScoringRequest
from backend.services.data_service import DataService


router = APIRouter(prefix="/api", tags=["scoring"])


@router.post("/score", response_model=list[CityMetrics])
def custom_score(
    request: ScoringRequest,
    service: DataService = Depends(get_data_service),
) -> list[dict]:
    return service.rescore(request.as_score_mapping())
