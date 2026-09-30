"""Tests for grounded AI routes without making Gemini API calls."""

import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from google.genai import errors
from pydantic import ValidationError

from backend.ai.gemini_service import (
    AIResponseError,
    AIServiceError,
    GeminiService,
)
from backend.ai.models import (
    AskMarketLensResponse,
    CityComparisonResponse,
    ExecutiveInsightsResponse,
)
from backend.api.dependencies import get_ai_service
from backend.api.main import app


class MockGeminiService:
    def __init__(self) -> None:
        self.last_context = None
        self.last_question = None

    def executive_insights(self, context: dict) -> ExecutiveInsightsResponse:
        self.last_context = context
        return ExecutiveInsightsResponse(
            executive_summary="Quito leads the current prioritization model.",
            key_findings=[
                {
                    "title": "Activity leadership",
                    "explanation": "Quito has the strongest supplied activity scores.",
                }
            ],
            opportunities=["Evaluate the leading cities through additional due diligence."],
            risks_and_caveats=["MarketLens does not contain profitability data."],
            recommended_next_steps=["Add financial and location-level analysis."],
        )

    def compare_cities(self, context: dict) -> CityComparisonResponse:
        self.last_context = context
        return CityComparisonResponse(
            city_a=context["city_a"]["city"],
            city_b=context["city_b"]["city"],
            summary="The current weights favor the stronger activity profile.",
            advantages_city_a=["Higher supplied sales score."],
            advantages_city_b=["Higher supplied growth score."],
            main_tradeoffs=["Current activity versus recent growth."],
            management_interpretation="Use the comparison to prioritize further research.",
        )

    def ask(self, question: str, context: dict) -> AskMarketLensResponse:
        self.last_question = question
        self.last_context = context
        return AskMarketLensResponse(
            answer="The ranking reflects the supplied component scores and weights.",
            supporting_points=["Sales per store has a 40% weight."],
            cities_referenced=["Quito", "Atlantis", "Cuenca"],
            caveat="This is decision support, not an investment recommendation.",
        )


class FailingGeminiService(MockGeminiService):
    def executive_insights(self, context: dict) -> ExecutiveInsightsResponse:
        raise AIServiceError("Gemini is temporarily unavailable.")


class AiApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)

    def setUp(self) -> None:
        self.mock_ai = MockGeminiService()
        app.dependency_overrides[get_ai_service] = lambda: self.mock_ai

    def tearDown(self) -> None:
        app.dependency_overrides.pop(get_ai_service, None)

    def test_executive_insights_endpoint_uses_top_five_context(self) -> None:
        response = self.client.post("/api/ai/insights")
        self.assertEqual(response.status_code, 200)
        self.assertIn("executive_summary", response.json())
        self.assertEqual(len(self.mock_ai.last_context["top_five_cities"]), 5)
        self.assertEqual(
            set(self.mock_ai.last_context["top_five_cities"][0]),
            {
                "city",
                "state",
                "opportunity_score",
                "sales_score",
                "transaction_score",
                "growth_score",
                "breadth_score",
                "active_stores",
            },
        )

    def test_city_comparison_endpoint_uses_actual_city_records(self) -> None:
        response = self.client.post(
            "/api/ai/compare", json={"city_a": "quito", "city_b": "Cuenca"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["city_a"], "Quito")
        self.assertEqual(self.mock_ai.last_context["city_b"]["city"], "Cuenca")

    def test_invalid_city_comparison_returns_404(self) -> None:
        response = self.client.post(
            "/api/ai/compare",
            json={"city_a": "Quito", "city_b": "Atlantis"},
        )
        self.assertEqual(response.status_code, 404)

    def test_ask_endpoint_receives_all_processed_cities(self) -> None:
        response = self.client.post(
            "/api/ai/ask", json={"question": "Why is Quito above Cuenca?"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.mock_ai.last_context["cities"]), 22)
        self.assertEqual(self.mock_ai.last_question, "Why is Quito above Cuenca?")
        self.assertEqual(response.json()["cities_referenced"], ["Quito", "Cuenca"])

    def test_empty_question_is_rejected(self) -> None:
        response = self.client.post("/api/ai/ask", json={"question": "   "})
        self.assertEqual(response.status_code, 422)

    def test_gemini_service_failure_returns_clean_502(self) -> None:
        app.dependency_overrides[get_ai_service] = FailingGeminiService
        response = self.client.post("/api/ai/insights")
        self.assertEqual(response.status_code, 502)
        self.assertIn("temporarily unavailable", response.json()["detail"])

    def test_missing_api_key_is_detected_before_network_call(self) -> None:
        service = GeminiService(api_key="")
        app.dependency_overrides[get_ai_service] = lambda: service
        response = self.client.post("/api/ai/insights")
        self.assertEqual(response.status_code, 503)
        self.assertIn("GEMINI_API_KEY", response.json()["detail"])

    def test_structured_response_validation_rejects_missing_sections(self) -> None:
        with self.assertRaises(ValidationError):
            ExecutiveInsightsResponse.model_validate(
                {"executive_summary": "Incomplete response"}
            )

    def test_provider_error_logging_is_diagnostic_and_redacted(self) -> None:
        api_key = "AIza" + "A" * 35
        provider_error = errors.APIError(
            429,
            {
                "error": {
                    "message": (
                        f"Quota exceeded for api_key={api_key} "
                        "authorization=Bearer sensitive-token"
                    ),
                    "status": "RESOURCE_EXHAUSTED",
                }
            },
        )
        service = GeminiService(api_key=api_key, model="gemini-3.8-flash")

        with patch("google.genai.Client") as client_class, patch(
            "backend.ai.gemini_service.time.sleep"
        ):
            client_class.return_value.models.generate_content.side_effect = provider_error
            with self.assertLogs("backend.ai.gemini_service", level="ERROR") as logs:
                with self.assertRaises(AIServiceError):
                    service._generate("diagnostic test", CityComparisonResponse)

        rendered_log = " ".join(logs.output)
        self.assertIn("category=APIError", rendered_log)
        self.assertIn("provider_status=429", rendered_log)
        self.assertIn("RESOURCE_EXHAUSTED", rendered_log)
        self.assertIn("[REDACTED]", rendered_log)
        self.assertNotIn(api_key, rendered_log)
        self.assertNotIn("sensitive-token", rendered_log)

    def test_transient_provider_error_retries_then_succeeds(self) -> None:
        transient_error = errors.APIError(
            503,
            {"error": {"message": "High demand", "status": "UNAVAILABLE"}},
        )
        expected = CityComparisonResponse(
            city_a="Quito",
            city_b="Cuenca",
            summary="Quito leads under the supplied weights.",
            advantages_city_a=["Higher activity scores."],
            advantages_city_b=["Higher growth score."],
            main_tradeoffs=["Current activity versus growth."],
            management_interpretation="Prioritize additional due diligence.",
        )
        response = Mock(parsed=expected, text=None)
        service = GeminiService(api_key="test-key", timeout_seconds=10)

        with patch("google.genai.Client") as client_class, patch(
            "backend.ai.gemini_service.random.uniform", return_value=0.1
        ), patch("backend.ai.gemini_service.time.sleep") as sleep:
            generate = client_class.return_value.models.generate_content
            generate.side_effect = [transient_error, response]
            result = service._generate("diagnostic test", CityComparisonResponse)

        self.assertEqual(result, expected)
        self.assertEqual(generate.call_count, 2)
        sleep.assert_called_once_with(0.6)

    def test_transient_provider_error_stops_after_two_retries(self) -> None:
        transient_error = errors.APIError(
            503,
            {"error": {"message": "High demand", "status": "UNAVAILABLE"}},
        )
        service = GeminiService(api_key="test-key", timeout_seconds=10)

        with patch("google.genai.Client") as client_class, patch(
            "backend.ai.gemini_service.random.uniform", return_value=0.0
        ), patch("backend.ai.gemini_service.time.sleep") as sleep:
            generate = client_class.return_value.models.generate_content
            generate.side_effect = transient_error
            with self.assertRaises(AIServiceError):
                service._generate("diagnostic test", CityComparisonResponse)

        self.assertEqual(generate.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_permanent_provider_error_is_not_retried(self) -> None:
        permanent_error = errors.APIError(
            401,
            {"error": {"message": "Invalid credentials", "status": "UNAUTHENTICATED"}},
        )
        service = GeminiService(api_key="test-key", timeout_seconds=10)

        with patch("google.genai.Client") as client_class, patch(
            "backend.ai.gemini_service.time.sleep"
        ) as sleep:
            generate = client_class.return_value.models.generate_content
            generate.side_effect = permanent_error
            with self.assertRaises(AIServiceError):
                service._generate("diagnostic test", CityComparisonResponse)

        self.assertEqual(generate.call_count, 1)
        sleep.assert_not_called()

    def test_retry_is_skipped_when_total_deadline_cannot_fit_delay(self) -> None:
        transient_error = errors.APIError(
            503,
            {"error": {"message": "High demand", "status": "UNAVAILABLE"}},
        )
        service = GeminiService(api_key="test-key", timeout_seconds=1)

        with patch("google.genai.Client") as client_class, patch(
            "backend.ai.gemini_service.random.uniform", return_value=0.0
        ), patch(
            "backend.ai.gemini_service.time.monotonic",
            side_effect=[0.0, 0.0, 0.75],
        ), patch("backend.ai.gemini_service.time.sleep") as sleep:
            generate = client_class.return_value.models.generate_content
            generate.side_effect = transient_error
            with self.assertRaises(AIServiceError):
                service._generate("diagnostic test", CityComparisonResponse)

        self.assertEqual(generate.call_count, 1)
        sleep.assert_not_called()

    def test_retry_after_header_sets_minimum_delay(self) -> None:
        response_headers = Mock(headers={"retry-after": "2"})
        transient_error = errors.APIError(
            429,
            {"error": {"message": "Rate limited", "status": "RESOURCE_EXHAUSTED"}},
            response=response_headers,
        )
        expected = CityComparisonResponse(
            city_a="Quito",
            city_b="Cuenca",
            summary="Comparison completed.",
            advantages_city_a=["Activity."],
            advantages_city_b=["Growth."],
            main_tradeoffs=["Activity versus growth."],
            management_interpretation="Continue due diligence.",
        )
        service = GeminiService(api_key="test-key", timeout_seconds=10)

        with patch("google.genai.Client") as client_class, patch(
            "backend.ai.gemini_service.random.uniform", return_value=0.1
        ), patch("backend.ai.gemini_service.time.sleep") as sleep:
            generate = client_class.return_value.models.generate_content
            generate.side_effect = [transient_error, Mock(parsed=expected, text=None)]
            service._generate("diagnostic test", CityComparisonResponse)

        sleep.assert_called_once_with(2.1)

    def test_structured_response_failure_logs_schema_without_response_body(self) -> None:
        service = GeminiService(api_key="test-key", model="gemini-3.8-flash")

        with patch("google.genai.Client") as client_class:
            response = client_class.return_value.models.generate_content.return_value
            response.parsed = None
            response.text = '{"summary": "secret response body"}'
            with self.assertLogs("backend.ai.gemini_service", level="ERROR") as logs:
                with self.assertRaises(AIResponseError):
                    service._generate("diagnostic test", CityComparisonResponse)

        rendered_log = " ".join(logs.output)
        self.assertIn("schema=CityComparisonResponse", rendered_log)
        self.assertNotIn("secret response body", rendered_log)


if __name__ == "__main__":
    unittest.main()
