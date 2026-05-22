"""Permission monitor + alerts endpoint tests."""
from datetime import datetime, timedelta

import pytest

from app.models.user import ClassifiedUser, UserCategory
from app.services.analysis_service import AnalysisResult
from app.services.data_providers.base import CollectedSnapshot
from app.services.permission_monitor import PermissionMonitor


def _user(**kwargs) -> ClassifiedUser:
    defaults = dict(
        id="005Sb0000012345AAA",
        username="x@y.z",
        full_name="X Y",
        license_type="Sales Cloud",
        profile_name="Standard User",
        last_login_date=datetime.utcnow() - timedelta(days=120),
        activity_score=5,
        category=UserCategory.INACTIVE,
    )
    defaults.update(kwargs)
    return ClassifiedUser(**defaults)


def _result(users) -> AnalysisResult:
    return AnalysisResult(
        org_id="t",
        snapshot=CollectedSnapshot(org_id="t"),
        classified=users,
        recommendations_by_user={},
        computed_at=datetime.utcnow(),
    )


def test_orphan_admin_critical():
    user = _user(profile_name="System Administrator")
    alerts = PermissionMonitor().scan(_result([user]))
    assert any(a.severity == "CRITICAL" and a.permission == "orphan_admin" for a in alerts)


def test_unused_high_value_license_high():
    user = _user(activity_score=0, license_type="Salesforce")
    alerts = PermissionMonitor().scan(_result([user]))
    assert any(a.severity == "HIGH" and a.permission == "unused_high_value_license" for a in alerts)


def test_efficient_user_no_alert():
    user = _user(
        activity_score=90,
        category=UserCategory.EFFICIENT,
        last_login_date=datetime.utcnow(),
    )
    alerts = PermissionMonitor().scan(_result([user]))
    assert alerts == []


def test_alerts_endpoint(client):
    response = client.get("/api/v1/alerts/test-org")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["org_id"] == "test-org"
    assert data["total"] == len(data["alerts"])
    assert isinstance(data["by_severity"], dict)
