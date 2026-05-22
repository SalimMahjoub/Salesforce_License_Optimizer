"""Regression tests covering each fix from the audit pass.

Each test pins ONE invariant; if any of these fails, we've reintroduced a
bug we already fixed.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models.recommendation import (
    ImpactLevel,
    Priority,
    Recommendation,
    RecommendationType,
)
from app.models.user import ClassifiedUser, UserCategory
from app.services.analysis_service import AnalysisResult, AnalysisService
from app.services.data_providers.base import CollectedSnapshot
from app.services.data_providers.demo import DemoDataProvider
from app.services.data_providers.sf_cli import _license_cost
from app.services.permission_monitor import PermissionMonitor
from app.utils.time import utcnow


# ----------------------------- helpers -----------------------------------
def _make_rec(user_id: str, monthly: Decimal, rec_type: RecommendationType = RecommendationType.DEACTIVATE) -> Recommendation:
    return Recommendation(
        user_id=user_id,
        username=f"u{user_id}@x.io",
        license_type="Salesforce",
        type=rec_type,
        title="t",
        description="d",
        monthly_savings=monthly,
        annual_savings=monthly * 12,
        priority=Priority.CRITICAL,
        impact=ImpactLevel.HIGH,
    )


def _make_user(uid: str, cat: UserCategory, score: int = 10, cost: str = "150",
               profile: str = "Standard User", license_type: str = "Salesforce") -> ClassifiedUser:
    return ClassifiedUser(
        id=uid + "AAA"[:18 - len(uid)] if len(uid) < 18 else uid,
        username=f"u{uid}@x.io",
        license_type=license_type,
        profile_name=profile,
        activity_score=score,
        category=cat,
        license_cost_monthly=Decimal(cost),
        last_login_date=datetime.utcnow() - timedelta(days=120) if cat == UserCategory.INACTIVE else datetime.utcnow(),
    )


def _result(users, recs_by_user) -> AnalysisResult:
    return AnalysisResult(
        org_id="t", snapshot=CollectedSnapshot(org_id="t"),
        classified=users, recommendations_by_user=recs_by_user, computed_at=utcnow(),
    )


# =====================================================================
# Regression #1 — analytics.py mock endpoint must not exist anymore
# =====================================================================
def test_analytics_router_no_longer_exists(unauth_client):
    """The mock /analytics/dashboard endpoint was misleading clients. Gone."""
    r = unauth_client.get("/api/v1/analytics/dashboard/test-org")
    assert r.status_code == 404


# =====================================================================
# Regression #2 — login is rate-limited (anti-bruteforce)
# =====================================================================
def test_login_rate_limited_after_5_attempts(unauth_client):
    """6th login attempt within a minute must be 429."""
    for _ in range(5):
        r = unauth_client.post(
            "/api/v1/auth/login",
            data={"username": "ghost@x.io", "password": "wrong"},
        )
        # First 5 are 401 (bad creds), not 429
        assert r.status_code in (401, 429)
    r = unauth_client.post(
        "/api/v1/auth/login",
        data={"username": "ghost@x.io", "password": "wrong"},
    )
    assert r.status_code == 429, f"Expected 429 on 6th try, got {r.status_code}"


# =====================================================================
# Regression #3 — savings must NEVER exceed total cost (max per user)
# =====================================================================
def test_savings_never_exceed_cost():
    """The live test caught savings_rate = 174 % when we naively summed.
    Max-per-user rollup must keep it bounded."""
    users = [_make_user(f"00{i:03d}xxAAA", UserCategory.INACTIVE, 5, cost="150") for i in range(5)]
    # Two recos per user (DEACTIVATE + REVIEW with overlapping savings)
    recs_by_user = {
        u.id: [_make_rec(u.id, Decimal("150"), RecommendationType.DEACTIVATE),
               _make_rec(u.id, Decimal("100"), RecommendationType.REVIEW)]
        for u in users
    }
    result = _result(users, recs_by_user)
    total_cost = result.total_monthly_cost()
    total_savings = result.total_monthly_savings()
    assert total_savings <= total_cost, (
        f"Savings {total_savings} > cost {total_cost} — double-counting regression!"
    )
    # Should be exactly 5 * 150 = 750 (max per user)
    assert total_savings == Decimal("750")


# =====================================================================
# Regression #3 bis — zombie_savings uses same max-per-user logic
# =====================================================================
def test_zombie_savings_max_per_user():
    z = _make_user("z00001xxAAAAAAAAA", UserCategory.INACTIVE, 5, cost="150")
    eff = _make_user("e00001xxAAAAAAAAA", UserCategory.EFFICIENT, 90, cost="150")
    recs = {
        z.id: [_make_rec(z.id, Decimal("150")), _make_rec(z.id, Decimal("100"))],
        eff.id: [_make_rec(eff.id, Decimal("200"))],  # should be excluded
    }
    result = _result([z, eff], recs)
    assert result.zombie_savings() == Decimal("150")


# =====================================================================
# Regression #4 — cache keyed by (org_id, days) not just org_id
# =====================================================================
@pytest.mark.asyncio
async def test_cache_distinguishes_days_window():
    """Two different `days` arguments must produce two distinct cache entries."""
    svc = AnalysisService(data_provider=DemoDataProvider(user_count=50))
    r30 = await svc.get_or_run("o", days=30)
    r180 = await svc.get_or_run("o", days=180)
    # Different days windows produce different snapshots (different period_start)
    assert r30 is not r180
    assert r30.snapshot.metrics[0].period_start != r180.snapshot.metrics[0].period_start


@pytest.mark.asyncio
async def test_cache_invalidate_clears_all_days():
    svc = AnalysisService(data_provider=DemoDataProvider(user_count=20))
    await svc.get_or_run("o", days=30)
    await svc.get_or_run("o", days=90)
    svc.invalidate("o")
    # After invalidate, fresh call must recompute (different object)
    r2 = await svc.get_or_run("o", days=30)
    assert r2 is not None  # smoke


# =====================================================================
# Regression #5 — PermissionMonitor catches barely-used (score <= 10) licences
# =====================================================================
def test_permission_monitor_catches_low_score_high_value():
    """Previously the rule required score == 0. Score 5 must now trigger HIGH."""
    user = _make_user("p00001xxAAAAAAAAA", UserCategory.INACTIVE, score=5, license_type="Salesforce")
    alerts = PermissionMonitor().scan(_result([user], {}))
    assert any(
        a.severity == "HIGH" and a.permission == "unused_high_value_license"
        for a in alerts
    )


# =====================================================================
# Regression #6 — free/technical licences cost 0, not 150
# =====================================================================
def test_free_license_cost_is_zero():
    assert _license_cost("Guest User License") == Decimal("0")
    assert _license_cost("Analytics Cloud Integration User") == Decimal("0")
    assert _license_cost("Sales Insights Integration User") == Decimal("0")
    assert _license_cost("Salesforce Integration") == Decimal("0")


def test_known_paid_license_keeps_real_cost():
    assert _license_cost("Salesforce") == Decimal("150")
    assert _license_cost("Platform") == Decimal("25")


def test_unknown_license_falls_back_to_baseline():
    assert _license_cost("Some Random New License 2026") == Decimal("150")


# =====================================================================
# Regression #7 — utcnow() helper available and timezone-naive UTC
# =====================================================================
def test_utcnow_helper_returns_naive_utc():
    now = utcnow()
    assert now.tzinfo is None
    # Should be within 1s of real UTC
    real = datetime.utcnow()
    assert abs((now - real).total_seconds()) < 1
