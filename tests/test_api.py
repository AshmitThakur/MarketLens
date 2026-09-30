"""API contract tests for MarketLens Phase 2."""

import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.main import app


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"status": "ok", "service": "MarketLens API"}
        )

    def test_overview_endpoint(self) -> None:
        response = self.client.get("/api/overview")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_stores"], 54)
        self.assertEqual(body["cities_analyzed"], 22)
        self.assertEqual(body["top_opportunity"]["city"], "Quito")
        self.assertEqual(
            body["analysis_period"],
            {"start": "2016-08-16", "end": "2017-08-15"},
        )

    def test_cities_endpoint_is_ranked_and_limited(self) -> None:
        response = self.client.get("/api/cities", params={"limit": 3})
        self.assertEqual(response.status_code, 200)
        cities = response.json()
        self.assertEqual(len(cities), 3)
        scores = [city["opportunity_score"] for city in cities]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_city_detail_lookup_is_case_insensitive(self) -> None:
        response = self.client.get("/api/cities/quito")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["city"], "Quito")
        self.assertEqual(body["weights"]["sales_weight"], 0.4)

    def test_invalid_city_returns_404(self) -> None:
        response = self.client.get("/api/cities/not-a-real-city")
        self.assertEqual(response.status_code, 404)

    def test_custom_scoring_uses_existing_component_scores(self) -> None:
        response = self.client.post(
            "/api/score",
            json={
                "sales_weight": 1.0,
                "transaction_weight": 0.0,
                "growth_weight": 0.0,
                "breadth_weight": 0.0,
            },
        )
        self.assertEqual(response.status_code, 200)
        cities = response.json()
        self.assertEqual(cities[0]["sales_score"], 100.0)
        self.assertEqual(
            cities[0]["opportunity_score"], cities[0]["sales_score"]
        )

    def test_invalid_weight_total_is_rejected(self) -> None:
        response = self.client.post(
            "/api/score",
            json={
                "sales_weight": 0.5,
                "transaction_weight": 0.5,
                "growth_weight": 0.5,
                "breadth_weight": 0.5,
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("weights must sum to 1.0", response.text)

    def test_state_filtering_is_case_insensitive(self) -> None:
        response = self.client.get("/api/cities", params={"state": "pichincha"})
        self.assertEqual(response.status_code, 200)
        cities = response.json()
        self.assertGreater(len(cities), 0)
        self.assertTrue(all(city["state"] == "Pichincha" for city in cities))

    def test_states_endpoint(self) -> None:
        response = self.client.get("/api/states")
        self.assertEqual(response.status_code, 200)
        states = response.json()
        self.assertEqual(len(states), 16)
        self.assertEqual(sum(state["stores"] for state in states), 54)

    def test_documented_frontend_origin_is_allowed_by_cors(self) -> None:
        response = self.client.options(
            "/api/overview",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://127.0.0.1:5173",
        )

    def test_cors_origins_can_be_configured_for_deployment(self) -> None:
        from backend.api.main import configured_cors_origins

        with patch.dict(
            "os.environ",
            {
                "FRONTEND_URL": "",
                "CORS_ORIGINS": "https://marketlens.vercel.app, https://preview.example",
            },
        ):
            origins = configured_cors_origins()
            self.assertIn("http://localhost:5173", origins)
            self.assertIn("http://127.0.0.1:5173", origins)
            self.assertIn("https://marketlens.vercel.app", origins)
            self.assertIn("https://preview.example", origins)

    def test_frontend_url_is_allowed_and_normalized_for_production(self) -> None:
        from backend.api.main import configured_cors_origins

        with patch.dict(
            "os.environ",
            {
                "FRONTEND_URL": "https://market-lens-livid-rho.vercel.app/",
                "CORS_ORIGINS": "",
            },
        ):
            origins = configured_cors_origins()
            self.assertIn("https://market-lens-livid-rho.vercel.app", origins)
            self.assertNotIn("https://market-lens-livid-rho.vercel.app/", origins)
            self.assertIn("http://localhost:3000", origins)
            self.assertIn("http://127.0.0.1:5173", origins)

    def test_environment_file_is_resolved_from_project_root(self) -> None:
        from backend.api.dependencies import ENV_FILE, PROJECT_ROOT

        expected_root = Path(__file__).resolve().parents[1]
        self.assertEqual(PROJECT_ROOT, expected_root)
        self.assertEqual(ENV_FILE, expected_root / ".env")
        self.assertTrue(ENV_FILE.is_absolute())

    def test_ai_service_reads_environment_after_initialization(self) -> None:
        from backend.api.dependencies import get_ai_service

        get_ai_service.cache_clear()
        try:
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test-only-key"}):
                service = get_ai_service()
                self.assertEqual(service.api_key, "test-only-key")
        finally:
            get_ai_service.cache_clear()


if __name__ == "__main__":
    unittest.main()
