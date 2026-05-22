"""Analysis service: the end-to-end pipeline that powers the dashboard.

Pipeline: DataProvider.collect → ClassificationService.classify_users
          → RecommendationFactory → aggregation for the UI.

Kept dependency-injected so demo / SF providers and scoring strategies stay
swappable, and so tests can pass deterministic inputs.

Results are cached in-process (per org_id) with a short TTL — re-running the
full pipeline on every dashboard refresh would be wasteful given the demo
provider generates 800 users on each call.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from app.factories.recommendation_factory import RecommendationFactory, recommendation_factory
from app.models.recommendation import Recommendation
from app.models.user import ClassifiedUser, UserCategory
from app.services.classification_service import ClassificationService, classification_service
from app.services.data_providers import CollectedSnapshot, DataProvider, get_data_provider
from app.utils.time import utcnow

logger = logging.getLogger(__name__)

_CACHE_TTL = timedelta(minutes=5)


@dataclass
class AnalysisResult:
    """Materialized analysis output kept warm in memory."""

    org_id: str
    snapshot: CollectedSnapshot
    classified: List[ClassifiedUser]
    recommendations_by_user: Dict[str, List[Recommendation]]
    computed_at: datetime

    # ---- aggregations ----------------------------------------------------

    def counts_by_category(self) -> Dict[str, int]:
        out: Dict[str, int] = {c.value: 0 for c in UserCategory}
        for u in self.classified:
            out[u.category.value] += 1
        return out

    def zombies(self) -> List[ClassifiedUser]:
        return [u for u in self.classified if u.category == UserCategory.INACTIVE]

    def total_monthly_cost(self) -> Decimal:
        return sum(
            (u.license_cost_monthly for u in self.classified),
            Decimal("0"),
        )

    def total_monthly_savings(self) -> Decimal:
        """Sum of the BEST cost-reducing rec per user.

        Important: each user often has several overlapping recommendations
        (e.g. DEACTIVATE + REVIEW). Summing them would double-count and
        produce nonsensical savings rates > 100 %. We keep the maximum
        monthly_savings per user as the realistic upper bound.
        """
        total = Decimal("0")
        for recs in self.recommendations_by_user.values():
            if not recs:
                continue
            total += max((r.monthly_savings for r in recs), default=Decimal("0"))
        return total

    def zombie_savings(self) -> Decimal:
        """Best per-user savings restricted to INACTIVE users."""
        zombie_ids = {u.id for u in self.zombies()}
        total = Decimal("0")
        for uid, recs in self.recommendations_by_user.items():
            if uid not in zombie_ids or not recs:
                continue
            total += max((r.monthly_savings for r in recs), default=Decimal("0"))
        return total


class AnalysisService:
    """Coordinates collection, classification and recommendation generation."""

    def __init__(
        self,
        data_provider: Optional[DataProvider] = None,
        classifier: Optional[ClassificationService] = None,
        factory: Optional[RecommendationFactory] = None,
    ):
        self._data_provider = data_provider or get_data_provider()
        self._classifier = classifier or classification_service
        self._factory = factory or recommendation_factory
        # Cache keyed by (org_id, days) — two different windows must NOT share
        # the same snapshot.
        self._cache: Dict[Tuple[str, int], AnalysisResult] = {}
        # One lock per (org_id, days) to avoid stampedes without serialising
        # unrelated tenants.
        self._locks: Dict[Tuple[str, int], asyncio.Lock] = {}

    def _lock_for(self, key: Tuple[str, int]) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    def _fresh(self, result: Optional[AnalysisResult]) -> bool:
        if result is None:
            return False
        return (utcnow() - result.computed_at) < _CACHE_TTL

    async def get_or_run(
        self,
        org_id: str,
        days: int = 90,
        force_refresh: bool = False,
    ) -> AnalysisResult:
        """Return a fresh-enough analysis, recomputing only if cache is stale."""
        key = (org_id, days)
        if not force_refresh and self._fresh(self._cache.get(key)):
            return self._cache[key]

        async with self._lock_for(key):
            # Re-check under lock to avoid stampedes
            if not force_refresh and self._fresh(self._cache.get(key)):
                return self._cache[key]
            result = await self._run(org_id, days)
            self._cache[key] = result
            return result

    async def _run(self, org_id: str, days: int) -> AnalysisResult:
        logger.info("Running full analysis pipeline for org=%s (days=%d)", org_id, days)
        snapshot = await self._data_provider.collect(org_id, days)

        classified = await self._classifier.classify_users(
            users=snapshot.users,
            metrics=snapshot.metrics,
        )

        metrics_by_user = {m.user_id: m for m in snapshot.metrics}
        recs_by_user: Dict[str, List[Recommendation]] = {}
        for user in classified:
            metric = metrics_by_user.get(user.id)
            if not metric:
                continue
            recs_by_user[user.id] = self._factory.create_recommendations(user, metric)

        logger.info(
            "Analysis done for org=%s: users=%d zombies=%d total_recs=%d",
            org_id,
            len(classified),
            sum(1 for u in classified if u.category == UserCategory.INACTIVE),
            sum(len(v) for v in recs_by_user.values()),
        )

        return AnalysisResult(
            org_id=org_id,
            snapshot=snapshot,
            classified=classified,
            recommendations_by_user=recs_by_user,
            computed_at=utcnow(),
        )

    def invalidate(self, org_id: Optional[str] = None) -> None:
        """Drop cache entries. ``None`` clears everything; otherwise only the
        given org's entries (across all ``days`` windows) are removed."""
        if org_id is None:
            self._cache.clear()
            return
        for key in list(self._cache.keys()):
            if key[0] == org_id:
                self._cache.pop(key, None)


# Default singleton wired with the configured DataProvider
analysis_service = AnalysisService()
