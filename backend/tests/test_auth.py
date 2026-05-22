"""Tests for JWT auth + multi-tenant guard."""
from app.services.security_service import create_access_token


class TestLogin:
    def test_login_success(self, unauth_client):
        response = unauth_client.post(
            "/api/v1/auth/login",
            data={"username": "demo@uprizon.io", "password": "demo-password"},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["access_token"]
        assert data["tenant_id"] == "demo"
        assert data["email"] == "demo@uprizon.io"

    def test_login_wrong_password(self, unauth_client):
        response = unauth_client.post(
            "/api/v1/auth/login",
            data={"username": "demo@uprizon.io", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_login_unknown_email(self, unauth_client):
        response = unauth_client.post(
            "/api/v1/auth/login",
            data={"username": "ghost@nowhere.io", "password": "anything"},
        )
        assert response.status_code == 401


class TestTokenGuards:
    def test_protected_endpoint_without_token_returns_401(self, unauth_client):
        response = unauth_client.get("/api/v1/analysis/test-org/dashboard")
        assert response.status_code == 401

    def test_protected_endpoint_with_wrong_tenant_returns_403(self, unauth_client):
        token = create_access_token(subject="x@y.z", tenant_id="other-org")
        response = unauth_client.get(
            "/api/v1/analysis/test-org/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        assert "tenant" in response.json()["detail"].lower()

    def test_protected_endpoint_with_invalid_token_returns_401(self, unauth_client):
        response = unauth_client.get(
            "/api/v1/analysis/test-org/dashboard",
            headers={"Authorization": "Bearer totally-not-a-jwt"},
        )
        assert response.status_code == 401

    def test_whoami(self, demo_client):
        response = demo_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "demo"
        assert data["email"] == "demo@uprizon.io"
