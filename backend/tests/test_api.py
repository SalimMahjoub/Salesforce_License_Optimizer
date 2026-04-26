"""
Integration tests for API endpoints.
"""
import pytest


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["version"] == "1.0.0"


class TestAuthAPI:
    """Test authentication API."""
    
    def test_get_authorization_url(self, client):
        """Test getting OAuth authorization URL."""
        response = client.get("/api/v1/auth/authorize")
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "salesforce.com" in data["authorization_url"]


class TestAnalyticsAPI:
    """Test analytics API."""
    
    def test_get_dashboard(self, client):
        """Test getting analytics dashboard."""
        response = client.get("/api/v1/analytics/dashboard/test-org")
        assert response.status_code == 200
        data = response.json()
        assert "mrr" in data
        assert "ltv" in data
        assert "total_monthly_savings" in data
    
    def test_get_roi_metrics(self, client):
        """Test getting ROI metrics."""
        response = client.get("/api/v1/analytics/roi/test-org")
        assert response.status_code == 200
        data = response.json()
        assert "baseline_cost" in data
        assert "current_cost" in data
        assert "roi_percentage" in data

