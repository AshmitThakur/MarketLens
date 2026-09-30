"""Small, mockable wrapper around the Google Gen AI SDK."""

import os
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .models import (
    AskMarketLensResponse,
    CityComparisonResponse,
    ExecutiveInsightsResponse,
)
from .prompts import (
    SYSTEM_PROMPT,
    ask_marketlens_prompt,
    city_comparison_prompt,
    executive_insights_prompt,
)


ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class AIConfigurationError(RuntimeError):
    """Raised when Gemini is not configured."""


class AIServiceError(RuntimeError):
    """Raised when the upstream Gemini request fails."""


class AIResponseError(RuntimeError):
    """Raised when Gemini returns an invalid structured response."""


class GeminiService:
    """Generate grounded, schema-validated MarketLens interpretations."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        configured_timeout = timeout_seconds or float(
            os.getenv("GEMINI_TIMEOUT_SECONDS", "30")
        )
        self.timeout_ms = int(configured_timeout * 1000)

    def executive_insights(self, context: dict) -> ExecutiveInsightsResponse:
        return self._generate(
            executive_insights_prompt(context), ExecutiveInsightsResponse
        )

    def compare_cities(self, context: dict) -> CityComparisonResponse:
        return self._generate(city_comparison_prompt(context), CityComparisonResponse)

    def ask(self, question: str, context: dict) -> AskMarketLensResponse:
        return self._generate(
            ask_marketlens_prompt(question, context), AskMarketLensResponse
        )

    def _generate(
        self, prompt: str, response_model: type[ResponseModel]
    ) -> ResponseModel:
        if not self.api_key or self.api_key == "your_api_key_here":
            raise AIConfigurationError(
                "Gemini is not configured. Set GEMINI_API_KEY in the backend environment."
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=self.timeout_ms),
            )
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=response_model,
                ),
            )
        except AIConfigurationError:
            raise
        except Exception as error:
            raise AIServiceError(
                "Gemini is temporarily unavailable. The analytics dashboard remains available."
            ) from error

        try:
            if isinstance(response.parsed, response_model):
                return response.parsed
            if not response.text:
                raise ValueError("Gemini returned an empty response")
            return response_model.model_validate_json(response.text)
        except (ValidationError, ValueError, TypeError) as error:
            raise AIResponseError(
                "Gemini returned a response that did not match the expected structure."
            ) from error
