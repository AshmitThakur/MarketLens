"""Small, mockable wrapper around the Google Gen AI SDK."""

import logging
import os
import random
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
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
LOGGER = logging.getLogger(__name__)
TRANSIENT_PROVIDER_STATUSES = {429, 503}
MAX_PROVIDER_ATTEMPTS = 3
INITIAL_RETRY_DELAY_SECONDS = 0.5
MAX_RETRY_JITTER_SECONDS = 0.25


def _safe_provider_error_details(
    error: Exception, api_key: str
) -> tuple[str, int | str | None, str | None, str]:
    """Extract useful provider diagnostics without exposing credentials."""
    category = type(error).__name__
    status = getattr(error, "code", None) or getattr(error, "status_code", None)
    reason = getattr(error, "status", None)
    description = getattr(error, "message", None) or str(error)
    description = str(description)

    if api_key:
        description = description.replace(api_key, "[REDACTED]")
    description = re.sub(
        r"(?i)Bearer\s+[^\s,;]+",
        "Bearer [REDACTED]",
        description,
    )
    description = re.sub(
        r"(?i)((?:api[_-]?key|x-goog-api-key|authorization|token|credential)"
        r"\s*[:=]\s*)[^\s,;]+",
        r"\1[REDACTED]",
        description,
    )
    description = re.sub(r"AIza[0-9A-Za-z_-]+", "[REDACTED]", description)
    description = " ".join(description.split())[:500]
    if not description:
        description = "No safe provider description was available."

    return category, status, reason, description


def _retry_after_seconds(error: Exception) -> float | None:
    """Read Retry-After headers from a provider error when available."""
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None

    retry_after_ms = headers.get("retry-after-ms")
    if retry_after_ms is not None:
        try:
            return max(0.0, float(retry_after_ms) / 1000)
        except (TypeError, ValueError):
            pass

    retry_after = headers.get("retry-after")
    if retry_after is None:
        return None
    try:
        return max(0.0, float(retry_after))
    except (TypeError, ValueError):
        try:
            retry_at = parsedate_to_datetime(str(retry_after))
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
        except (AttributeError, TypeError, ValueError, OverflowError):
            return None


def _retry_delay_seconds(error: Exception, failed_attempt: int) -> float:
    """Combine provider guidance with bounded exponential backoff and jitter."""
    exponential_delay = INITIAL_RETRY_DELAY_SECONDS * (2 ** (failed_attempt - 1))
    provider_delay = _retry_after_seconds(error) or 0.0
    jitter = random.uniform(0.0, MAX_RETRY_JITTER_SECONDS)
    return max(exponential_delay, provider_delay) + jitter


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
        self.timeout_seconds = configured_timeout
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
            LOGGER.error(
                "Gemini configuration error: category=missing_api_key model=%s",
                self.model,
            )
            raise AIConfigurationError(
                "Gemini is not configured. Set GEMINI_API_KEY in the backend environment."
            )

        try:
            from google import genai
            from google.genai import types

            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=response_model,
            )
            deadline = time.monotonic() + self.timeout_seconds

            for attempt in range(1, MAX_PROVIDER_ATTEMPTS + 1):
                remaining_seconds = deadline - time.monotonic()
                if remaining_seconds <= 0:
                    raise TimeoutError("Gemini request deadline was exhausted.")

                client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(
                        timeout=max(1, int(remaining_seconds * 1000)),
                        retry_options=types.HttpRetryOptions(attempts=1),
                    ),
                )
                try:
                    try:
                        response = client.models.generate_content(
                            model=self.model,
                            contents=prompt,
                            config=config,
                        )
                    finally:
                        client.close()
                    break
                except Exception as error:
                    status = getattr(error, "code", None) or getattr(
                        error, "status_code", None
                    )
                    if (
                        status not in TRANSIENT_PROVIDER_STATUSES
                        or attempt >= MAX_PROVIDER_ATTEMPTS
                    ):
                        raise

                    delay_seconds = _retry_delay_seconds(error, attempt)
                    remaining_seconds = deadline - time.monotonic()
                    if delay_seconds >= remaining_seconds:
                        raise

                    category, _, reason, description = _safe_provider_error_details(
                        error, self.api_key
                    )
                    LOGGER.warning(
                        "Gemini transient provider error; retrying: category=%s "
                        "provider_status=%s provider_reason=%s model=%s "
                        "failed_attempt=%s next_attempt=%s delay_seconds=%.2f "
                        "description=%s",
                        category,
                        status,
                        reason if reason is not None else "unavailable",
                        self.model,
                        attempt,
                        attempt + 1,
                        delay_seconds,
                        description,
                    )
                    time.sleep(delay_seconds)
        except AIConfigurationError:
            raise
        except Exception as error:
            category, status, reason, description = _safe_provider_error_details(
                error, self.api_key
            )
            LOGGER.error(
                "Gemini provider request failed: category=%s provider_status=%s "
                "provider_reason=%s model=%s description=%s",
                category,
                status if status is not None else "unavailable",
                reason if reason is not None else "unavailable",
                self.model,
                description,
            )
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
            error_count = error.error_count() if isinstance(error, ValidationError) else 1
            LOGGER.error(
                "Gemini structured response validation failed: category=%s model=%s "
                "schema=%s error_count=%s",
                type(error).__name__,
                self.model,
                response_model.__name__,
                error_count,
            )
            raise AIResponseError(
                "Gemini returned a response that did not match the expected structure."
            ) from error
