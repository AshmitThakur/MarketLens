"""Shared FastAPI dependencies."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from backend.ai.gemini_service import GeminiService
from backend.services.data_service import DataService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@lru_cache
def get_data_service() -> DataService:
    """Return the single in-process data cache used by API requests."""
    processed_dir = PROJECT_ROOT / "data" / "processed"
    return DataService(
        metrics_path=processed_dir / "city_metrics.csv",
        metadata_path=processed_dir / "analysis_metadata.json",
    )


@lru_cache
def get_ai_service() -> GeminiService:
    """Return the lazily configured backend-only Gemini service."""
    return GeminiService()
