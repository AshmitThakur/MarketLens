"""Shared FastAPI dependencies."""

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from backend.services.data_service import DataService

if TYPE_CHECKING:
    from backend.ai.gemini_service import GeminiService


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


def load_project_environment() -> None:
    """Load root environment settings without replacing process-level values."""
    load_dotenv(dotenv_path=ENV_FILE, override=False)


load_project_environment()


@lru_cache
def get_data_service() -> DataService:
    """Return the single in-process data cache used by API requests."""
    processed_dir = PROJECT_ROOT / "data" / "processed"
    return DataService(
        metrics_path=processed_dir / "city_metrics.csv",
        metadata_path=processed_dir / "analysis_metadata.json",
    )


@lru_cache
def get_ai_service() -> "GeminiService":
    """Return the lazily configured backend-only Gemini service."""
    # Keep environment initialization ahead of both import and construction.
    # The cached service still requires a process restart after configuration changes.
    load_project_environment()
    from backend.ai.gemini_service import GeminiService

    return GeminiService()
