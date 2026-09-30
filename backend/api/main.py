"""MarketLens FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.dependencies import get_data_service
from backend.api.routes import ai, cities, overview, scoring


DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:5173,http://127.0.0.1:5173"
)


def configured_cors_origins() -> list[str]:
    """Return local, deployed frontend, and optional extra browser origins."""
    candidates = [
        *DEFAULT_CORS_ORIGINS.split(","),
        os.getenv("FRONTEND_URL", ""),
        *os.getenv("CORS_ORIGINS", "").split(","),
    ]
    origins = [origin.strip().rstrip("/") for origin in candidates if origin.strip()]
    return list(dict.fromkeys(origins))


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Load processed analytics once when the application starts."""
    get_data_service().load()
    yield


app = FastAPI(
    title="MarketLens API",
    description="Retail expansion analytics for the MarketLens dashboard.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router)
app.include_router(cities.router)
app.include_router(scoring.router)
app.include_router(ai.router)
