"""Real Salesforce data provider.

Wires the existing OAuth + SOQL repositories into the DataProvider contract.
Activated when ``settings.data_provider == "salesforce"``.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

from app.models.license import LICENSE_CATALOG
from app.models.metrics import UserMetrics
from app.repositories.salesforce.login_repository import LoginEventRepository
from app.repositories.user_repository import UserRepository
from app.services.data_providers.base import CollectedSnapshot, DataProvider
from app.services.oauth_service import oauth_service
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


class SalesforceDataProvider(DataProvider):
    """Pulls data from a live Salesforce org via OAuth."""

    async def collect(self, org_id: str, days: int = 90) -> CollectedSnapshot:
        sf_client = await oauth_service.get_salesforce_client(org_id)
        user_repo = UserRepository(sf_client)
        login_repo = LoginEventRepository(sf_client)

        users = await user_repo.get_all()
        login_events = await login_repo.get_all(days=days)
        login_counts: dict[str, int] = {}
        for event in login_events:
            uid = event.get("UserId")
            if uid:
                login_counts[uid] = login_counts.get(uid, 0) + 1

        now = utcnow()
        period_start = (now - timedelta(days=days)).date()
        period_end = now.date()

        metrics: List[UserMetrics] = []
        for user in users:
            license_info = LICENSE_CATALOG.get(user.license_type)
            cost = license_info.monthly_cost if license_info else Decimal("150")
            metrics.append(
                UserMetrics(
                    user_id=user.id,
                    username=user.username,
                    license_type=user.license_type,
                    license_cost=cost,
                    period_start=period_start,
                    period_end=period_end,
                    last_login=user.last_login_date,
                    login_count_90d=login_counts.get(user.id, 0),
                    # Features & records require additional APIs (Phase 2.2)
                    features_used=set(),
                    total_features_available=100,
                    records_created=0,
                    records_modified=0,
                )
            )

        logger.info(
            "Salesforce snapshot for org=%s: %d users, %d login events",
            org_id, len(users), len(login_events),
        )
        return CollectedSnapshot(
            org_id=org_id,
            users=users,
            metrics=metrics,
            collected_at=now,
        )
