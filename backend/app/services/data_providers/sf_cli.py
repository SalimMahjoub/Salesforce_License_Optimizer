"""SF CLI-fed data provider.

Reads ``sf data query`` JSON exports from disk and adapts them to the
``DataProvider`` contract. This is what we use for live demos when we don't
want to install simple-salesforce locally — the sf CLI handles auth + SOQL,
this provider handles the mapping to our domain.

Expected files:
  artifacts/sf-users-raw.json   ← from: SELECT Id, Username, Email, FirstName,
                                            LastName, LastLoginDate, CreatedDate,
                                            UserType, Profile.Name,
                                            Profile.UserLicense.Name
                                     FROM User WHERE IsActive = TRUE
  artifacts/sf-logins-raw.json  ← from: SELECT UserId, COUNT(Id) login_count
                                     FROM LoginHistory WHERE LoginTime = LAST_N_DAYS:90
                                     GROUP BY UserId
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from app.models.license import LICENSE_CATALOG
from app.models.metrics import UserMetrics
from app.models.user import SfUser
from app.services.data_providers.base import CollectedSnapshot, DataProvider
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


# Map Salesforce licence names → keys in our LICENSE_CATALOG so cost rollups work.
_LICENSE_NAME_TO_CATALOG = {
    "Salesforce": "Salesforce",
    "Sales Cloud": "Sales Cloud",
    "Service Cloud": "Service Cloud",
    "Sales Cloud Einstein": "Sales Cloud Einstein",
    "Salesforce Platform": "Platform",
    "Platform": "Platform",
    "Force.com - One App": "Platform",
    "Chatter Free": "Chatter Free",
    "Identity": "Identity",
}

# Licences SF qui sont gratuites / techniques (ne pas compter dans le coût).
# Le but est de ne PAS surestimer le coût total en y mettant 150€ par défaut.
_FREE_OR_TECHNICAL_LICENSES = {
    "Guest User License",
    "Analytics Cloud Integration User",
    "Sales Insights Integration User",
    "SalesforceIQ Integration User",
    "Einstein Agent",
    "Salesforce Integration",
    "Chatter Free",          # gratuit côté Salesforce
    "Identity",              # gratuit jusqu'à 10 utilisateurs
    "Customer Community Login",  # facturé au login, pas au siège
}


def _coerce_id_to_18(sf_id: str) -> str:
    """SOAP/REST APIs return 18-char IDs by default; defensively handle 15-char."""
    if len(sf_id) == 15:
        return sf_id + "AAA"
    return sf_id


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    # Salesforce returns ISO 8601 with timezone; tolerate both Z and +HH:MM
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _license_cost(license_name: Optional[str]) -> Decimal:
    """Map an SF licence label to a monthly cost in EUR.

    Returns 0 for free/technical licences (Guest, Integration users, etc.) so
    they don't inflate the org's cost baseline.
    """
    if not license_name:
        return Decimal("150")
    if license_name in _FREE_OR_TECHNICAL_LICENSES:
        return Decimal("0")
    key = _LICENSE_NAME_TO_CATALOG.get(license_name)
    if key and key in LICENSE_CATALOG:
        return LICENSE_CATALOG[key].monthly_cost
    # Unknown commercial licence — fall back to the Salesforce baseline so the
    # finance team still sees a number, but log so we can extend the mapping.
    logger.info("Unknown SF licence %r — defaulting cost to 150 EUR/month", license_name)
    return Decimal("150")


class SfCliDataProvider(DataProvider):
    """Reads pre-pulled SOQL JSON files and serves them as a CollectedSnapshot."""

    def __init__(
        self,
        users_path: Path | str = "artifacts/sf-users-raw.json",
        logins_path: Path | str = "artifacts/sf-logins-raw.json",
    ):
        self.users_path = Path(users_path)
        self.logins_path = Path(logins_path)

    async def collect(self, org_id: str, days: int = 90) -> CollectedSnapshot:
        users_payload = json.loads(self.users_path.read_text(encoding="utf-8"))
        logins_payload = json.loads(self.logins_path.read_text(encoding="utf-8"))

        login_counts: dict[str, int] = {}
        for rec in logins_payload.get("result", {}).get("records", []):
            uid = rec.get("UserId")
            if uid:
                login_counts[_coerce_id_to_18(uid)] = int(rec.get("login_count") or 0)

        now = utcnow()
        period_start = (now - timedelta(days=days)).date()
        period_end = now.date()

        users: List[SfUser] = []
        metrics: List[UserMetrics] = []

        for rec in users_payload.get("result", {}).get("records", []):
            uid = _coerce_id_to_18(rec["Id"])
            profile = rec.get("Profile") or {}
            license_obj = profile.get("UserLicense") or {}
            license_name = license_obj.get("Name") or "Salesforce"

            full_name_parts = [rec.get("FirstName") or "", rec.get("LastName") or ""]
            full_name = " ".join(p for p in full_name_parts if p).strip() or None

            last_login = _parse_dt(rec.get("LastLoginDate"))
            created = _parse_dt(rec.get("CreatedDate"))

            user = SfUser(
                id=uid,
                username=rec["Username"],
                email=rec.get("Email"),
                full_name=full_name,
                license_type=license_name,
                profile_name=profile.get("Name") or "Unknown",
                last_login_date=last_login,
                created_date=created,
                user_type=rec.get("UserType") or "Standard",
            )
            users.append(user)

            cost = _license_cost(license_name)
            metrics.append(UserMetrics(
                user_id=uid,
                username=rec["Username"],
                license_type=license_name,
                license_cost=cost,
                period_start=period_start,
                period_end=period_end,
                last_login=last_login,
                login_count_90d=login_counts.get(uid, 0),
                features_used=set(),
                total_features_available=100,
                records_created=0,
                records_modified=0,
            ))

        logger.info(
            "SfCliDataProvider snapshot for org=%s: %d users, %d with login activity",
            org_id, len(users), len([m for m in metrics if m.login_count_90d > 0]),
        )
        return CollectedSnapshot(
            org_id=org_id, users=users, metrics=metrics, collected_at=now,
        )
