"""
Pytest configuration and fixtures.
"""
import pytest
import asyncio
from typing import Generator

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator:
    """Test client fixture."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_user_data():
    """Mock Salesforce user data."""
    return {
        "id": "005xx000001X8F3AAK",
        "username": "test.user@company.com",
        "email": "test.user@company.com",
        "full_name": "Test User",
        "is_active": True,
        "license_type": "Sales Cloud",
        "profile_name": "Standard User",
        "last_login_date": "2024-02-08",
        "created_date": "2023-01-15"
    }


@pytest.fixture
def mock_metrics():
    """Mock user metrics."""
    from app.models.metrics import UserMetrics
    from decimal import Decimal
    from datetime import date
    
    return UserMetrics(
        user_id="005xx000001X8F3AAK",
        username="test.user@company.com",
        license_type="Sales Cloud",
        license_cost=Decimal("150.00"),
        period_start=date(2024, 1, 1),
        period_end=date(2024, 2, 1),
        last_login=date(2024, 2, 8),
        login_count_90d=45,
        features_used={"Accounts", "Opportunities", "Reports"},
        total_features_available=100,
        records_created=25,
        records_modified=150
    )
