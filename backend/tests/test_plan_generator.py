"""Tests for the GPT-4-backed plan generator (fallback path only)."""
from decimal import Decimal

import pytest

from app.factories.recommendation_factory import RecommendationFactory
from app.models.user import UserCategory
from app.services.analysis_service import AnalysisService
from app.services.data_providers.demo import DemoDataProvider
from app.services.plan_generator import PlanGenerator, _fallback_plan


@pytest.mark.asyncio
async def test_fallback_plan_has_required_shape():
    plan = _fallback_plan([], Decimal("0"), Decimal("0"))
    assert plan.title
    assert len(plan.steps) >= 3
    assert plan.timeline


@pytest.mark.asyncio
async def test_plan_generator_falls_back_with_test_key():
    """With sk-test-* api key (set in conftest), generator must NOT call GPT."""
    svc = AnalysisService(data_provider=DemoDataProvider(user_count=100))
    result = await svc.get_or_run("plan-test-org")
    recs = [r for recs in result.recommendations_by_user.values() for r in recs]

    plan = await PlanGenerator().generate(
        recommendations=recs,
        org_name="Plan Test",
        total_users=len(result.classified),
    )

    assert plan.model_version == "fallback"
    assert plan.total_estimated_savings >= 0
    assert plan.annual_estimated_savings == plan.total_estimated_savings * 12
    # PlanGenerator still uses raw sum (not max-per-user) by design — it's the
    # GPT-4 prompt's role to consolidate. We just sanity-check it's positive.
