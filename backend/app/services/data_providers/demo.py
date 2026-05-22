"""Deterministic demo data provider.

Generates a realistic Salesforce org snapshot (800 users by default) with
plausible distribution across the 4 UserCategory buckets, so the whole
pipeline can be demonstrated end-to-end without any external dependency.

Distribution targets (CFO pitch from README):
    Zombies/Inactive : ~30%
    Underutilized    : ~25%
    Optimizable      : ~25%
    Efficient        : ~20%
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List

from app.models.license import LICENSE_CATALOG
from app.models.metrics import UserMetrics
from app.models.user import SfUser
from app.services.data_providers.base import CollectedSnapshot, DataProvider
from app.utils.time import utcnow


# 18-char Salesforce ID prefix for User sobject
_SF_ID_PREFIX = "005Sb00000"
_LICENSE_POOL = [
    "Sales Cloud",
    "Service Cloud",
    "Salesforce",
    "Platform",
]
_FIRST_NAMES = [
    "Marie", "Pierre", "Sophie", "Lucas", "Emma", "Hugo", "Camille",
    "Thomas", "Julie", "Antoine", "Léa", "Nicolas", "Chloé", "Maxime",
    "Sarah", "Romain", "Manon", "Florian", "Anaïs", "Vincent",
]
_LAST_NAMES = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard",
    "Petit", "Durand", "Leroy", "Moreau", "Simon", "Laurent",
    "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux",
]
_PROFILES = ["Standard User", "Sales Manager", "Service User", "System Administrator"]


def _make_sf_id(idx: int) -> str:
    """Generate a deterministic 18-char-looking Salesforce ID."""
    return f"{_SF_ID_PREFIX}{idx:05d}AAA"


class DemoDataProvider(DataProvider):
    """Generates fake but realistic Salesforce org data, deterministic per org_id."""

    def __init__(self, user_count: int = 800):
        self.user_count = user_count

    async def collect(self, org_id: str, days: int = 90) -> CollectedSnapshot:
        rng = random.Random(f"{org_id}::{self.user_count}")
        users: List[SfUser] = []
        metrics: List[UserMetrics] = []

        now = utcnow()
        period_start = (now - timedelta(days=days)).date()
        period_end = now.date()

        for i in range(self.user_count):
            user, metric = self._make_user(i, rng, now, period_start, period_end)
            users.append(user)
            metrics.append(metric)

        return CollectedSnapshot(
            org_id=org_id,
            users=users,
            metrics=metrics,
            collected_at=now,
        )

    def _make_user(
        self,
        idx: int,
        rng: random.Random,
        now: datetime,
        period_start: date,
        period_end: date,
    ) -> tuple[SfUser, UserMetrics]:
        # Bucket distribution: 30% inactive / 25% underutilized / 25% optimizable / 20% efficient
        bucket_roll = rng.random()
        if bucket_roll < 0.30:
            bucket = "inactive"
        elif bucket_roll < 0.55:
            bucket = "underutilized"
        elif bucket_roll < 0.80:
            bucket = "optimizable"
        else:
            bucket = "efficient"

        first = rng.choice(_FIRST_NAMES)
        last = rng.choice(_LAST_NAMES)
        username = f"{first.lower()}.{last.lower()}{idx}@demo-org.com"
        full_name = f"{first} {last}"
        license_type = rng.choices(
            _LICENSE_POOL,
            weights=[0.4, 0.2, 0.15, 0.25],
        )[0]
        profile = rng.choice(_PROFILES)
        license_cost = LICENSE_CATALOG[license_type].monthly_cost

        # Activity profile per bucket
        if bucket == "inactive":
            # Either never logged or 90+ days ago
            if rng.random() < 0.3:
                last_login = None
            else:
                last_login = now - timedelta(days=rng.randint(91, 540))
            login_count = rng.randint(0, 3)
            features = set(rng.sample(range(100), k=rng.randint(0, 5)))
            records_c, records_m = 0, rng.randint(0, 2)
        elif bucket == "underutilized":
            last_login = now - timedelta(days=rng.randint(15, 60))
            login_count = rng.randint(4, 15)
            features = set(rng.sample(range(100), k=rng.randint(10, 25)))
            records_c, records_m = rng.randint(0, 5), rng.randint(2, 15)
        elif bucket == "optimizable":
            last_login = now - timedelta(days=rng.randint(1, 20))
            login_count = rng.randint(20, 50)
            features = set(rng.sample(range(100), k=rng.randint(30, 55)))
            records_c, records_m = rng.randint(10, 40), rng.randint(20, 80)
        else:  # efficient
            last_login = now - timedelta(days=rng.randint(0, 5))
            login_count = rng.randint(60, 90)
            features = set(rng.sample(range(100), k=rng.randint(60, 95)))
            records_c, records_m = rng.randint(40, 120), rng.randint(80, 250)

        created_date = now - timedelta(days=rng.randint(60, 1500))

        user = SfUser(
            id=_make_sf_id(idx),
            username=username,
            email=username,
            full_name=full_name,
            license_type=license_type,
            profile_name=profile,
            last_login_date=last_login,
            created_date=created_date,
        )

        metric = UserMetrics(
            user_id=user.id,
            username=username,
            license_type=license_type,
            license_cost=Decimal(str(license_cost)),
            period_start=period_start,
            period_end=period_end,
            last_login=last_login,
            login_count_90d=login_count,
            features_used={f"feature_{n}" for n in features},
            total_features_available=100,
            records_created=records_c,
            records_modified=records_m,
        )

        return user, metric
