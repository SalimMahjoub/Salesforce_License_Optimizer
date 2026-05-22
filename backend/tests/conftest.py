"""Pytest configuration and fixtures.

Sets dummy env vars BEFORE importing app.main so Settings() never fails in CI
where no .env file exists. Provides two clients:
- ``client``  : authenticated as the demo user (tenant_id="demo")
- ``unauth_client`` : no Authorization header (for auth-failure tests)
"""
import os
from datetime import date
from decimal import Decimal
from typing import Generator

# --- Required env vars MUST be set before importing the app ---
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/test_db",
)
os.environ.setdefault("SF_CLIENT_ID", "test_client_id")
os.environ.setdefault("SF_CLIENT_SECRET", "test_client_secret")
os.environ.setdefault("SF_REDIRECT_URI", "http://localhost:8000/oauth/callback")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-real")
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-minimum-32-characters-long-for-jwt",
)
os.environ.setdefault(
    "ENCRYPTION_KEY",
    "zmWmS7p6gK1H7N0pXhVz9JmnJ8m4mY3o5p2WJZ6e1nQ=",
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services.security_service import create_access_token  # noqa: E402

# All demo tests target this tenant. Matches the seeded user in dependencies.py.
DEMO_TENANT = "demo"
DEMO_EMAIL = "demo@uprizon.io"
TEST_TENANT = "test-org"  # used by tests that hit /{org_id}/...


@pytest.fixture
def unauth_client() -> Generator:
    """TestClient without any Authorization header."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client() -> Generator:
    """TestClient pre-authenticated with a token whose tenant_id == 'test-org'.

    Most tests use /api/v1/.../test-org/... so we mint a token for that tenant.
    """
    token = create_access_token(subject=DEMO_EMAIL, tenant_id=TEST_TENANT)
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c


@pytest.fixture
def demo_client() -> Generator:
    """TestClient authenticated as demo@uprizon.io / tenant 'demo'."""
    token = create_access_token(subject=DEMO_EMAIL, tenant_id=DEMO_TENANT)
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c


@pytest.fixture
def mock_user_data() -> dict:
    return {
        "id": "005xx000001X8F3AAK",
        "username": "test.user@company.com",
        "email": "test.user@company.com",
        "full_name": "Test User",
        "is_active": True,
        "license_type": "Sales Cloud",
        "profile_name": "Standard User",
        "last_login_date": "2024-02-08",
        "created_date": "2023-01-15",
    }


@pytest.fixture
def mock_metrics():
    from app.models.metrics import UserMetrics

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
        records_modified=150,
    )
