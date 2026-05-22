"""Abstract data provider contract."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from app.models.metrics import UserMetrics
from app.models.user import SfUser
from app.utils.time import utcnow


@dataclass
class CollectedSnapshot:
    """One coherent view of an org at a point in time."""

    org_id: str
    users: List[SfUser] = field(default_factory=list)
    metrics: List[UserMetrics] = field(default_factory=list)
    collected_at: datetime = field(default_factory=utcnow)


class DataProvider(ABC):
    """Pluggable source of user + usage data for a Salesforce org."""

    @abstractmethod
    async def collect(self, org_id: str, days: int = 90) -> CollectedSnapshot:
        """Fetch users + metrics for the given org over the given window."""
