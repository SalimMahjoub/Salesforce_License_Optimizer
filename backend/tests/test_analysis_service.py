"""End-to-end tests for the analysis pipeline using the DemoDataProvider."""
import pytest

from app.models.user import UserCategory
from app.services.analysis_service import AnalysisService
from app.services.data_providers.demo import DemoDataProvider


@pytest.fixture
def analysis_service_demo() -> AnalysisService:
    """Fresh AnalysisService wired to a small deterministic demo org."""
    return AnalysisService(data_provider=DemoDataProvider(user_count=200))


@pytest.mark.asyncio
async def test_analysis_classifies_all_users(analysis_service_demo):
    result = await analysis_service_demo.get_or_run("test-org", days=90)
    assert len(result.classified) == 200
    assert all(u.activity_score >= 0 and u.activity_score <= 100 for u in result.classified)
    assert all(isinstance(u.category, UserCategory) for u in result.classified)


@pytest.mark.asyncio
async def test_demo_produces_realistic_distribution(analysis_service_demo):
    result = await analysis_service_demo.get_or_run("test-org", days=90)
    counts = result.counts_by_category()

    # The demo generator targets ~30% inactive — allow a wide tolerance to
    # avoid flakiness (deterministic per org_id but distribution drifts with
    # the scoring algorithm).
    inactive_share = counts[UserCategory.INACTIVE.value] / 200
    assert 0.15 < inactive_share < 0.60, counts


@pytest.mark.asyncio
async def test_zombies_have_savings(analysis_service_demo):
    result = await analysis_service_demo.get_or_run("test-org", days=90)
    zombies = result.zombies()
    assert len(zombies) > 0
    # Inactive users should have at least one recommendation reducing cost
    for z in zombies:
        recs = result.recommendations_by_user.get(z.id, [])
        assert any(r.monthly_savings > 0 for r in recs), (
            f"Zombie {z.id} has no cost-reducing recommendation"
        )


@pytest.mark.asyncio
async def test_cache_hit_returns_same_object(analysis_service_demo):
    a = await analysis_service_demo.get_or_run("test-org")
    b = await analysis_service_demo.get_or_run("test-org")
    assert a is b  # same cached AnalysisResult


@pytest.mark.asyncio
async def test_force_refresh_recomputes(analysis_service_demo):
    a = await analysis_service_demo.get_or_run("test-org")
    b = await analysis_service_demo.get_or_run("test-org", force_refresh=True)
    assert a is not b
    # But the data should be deterministic for the same org_id
    assert len(a.classified) == len(b.classified)
