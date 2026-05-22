"""HTTP-level tests for the /api/v1/analysis endpoints."""
import pytest


@pytest.fixture(autouse=True)
def _invalidate_cache():
    """Wipe analysis cache between tests so each starts clean."""
    from app.services.analysis_service import analysis_service
    analysis_service.invalidate()
    yield
    analysis_service.invalidate()


def test_dashboard_endpoint(client):
    response = client.get("/api/v1/analysis/test-org/dashboard")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["org_id"] == "test-org"
    assert data["total_users"] > 0
    assert "counts_by_category" in data
    assert {"inactive", "underutilized", "optimizable", "efficient"} <= set(
        data["counts_by_category"].keys()
    )


def test_zombies_endpoint(client):
    response = client.get("/api/v1/analysis/test-org/zombies")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["zombie_count"] == len(data["users"])
    for user in data["users"]:
        assert user["category"] == "inactive"


def test_users_endpoint_pagination(client):
    response = client.get("/api/v1/analysis/test-org/users?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) <= 10
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_users_endpoint_invalid_category(client):
    response = client.get("/api/v1/analysis/test-org/users?category=bogus")
    assert response.status_code == 400


def test_refresh_endpoint(client):
    response = client.post("/api/v1/analysis/test-org/refresh")
    assert response.status_code == 200
    assert "computed_at" in response.json()
