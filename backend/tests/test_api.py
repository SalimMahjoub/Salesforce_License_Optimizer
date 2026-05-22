"""Smoke tests for the top-level API surface."""


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


class TestRootEndpoint:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["version"] == "1.0.0"


class TestAuthAPI:
    def test_get_authorization_url(self, client):
        response = client.get("/api/v1/auth/authorize")
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "salesforce.com" in data["authorization_url"]


class TestRecommendationsAPI:
    def test_list_recommendations_demo(self, client):
        response = client.get("/api/v1/recommendations/test-org")
        assert response.status_code == 200
        data = response.json()
        assert data["org_id"] == "test-org"
        assert data["total"] >= 0
        assert "recommendations" in data


class TestReportsAPI:
    def test_cfo_plan_fallback(self, client):
        # Test key is sk-test-* → PlanGenerator uses fallback (no GPT call)
        response = client.get("/api/v1/reports/test-org/cfo-plan")
        assert response.status_code == 200
        data = response.json()
        assert data["title"]
        assert len(data["steps"]) >= 1
        assert data["model_version"] == "fallback"
