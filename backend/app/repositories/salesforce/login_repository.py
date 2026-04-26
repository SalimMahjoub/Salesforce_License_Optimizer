"""
Login Event Repository for tracking user login history.
"""
from typing import List, Dict
from datetime import datetime, timedelta

from app.repositories.salesforce.base import SalesforceRepository


class LoginEventRepository(SalesforceRepository[dict]):
    """Repository for Salesforce LoginEvent data."""
    
    QUERY_FIELDS = [
        "UserId",
        "EventType",
        "CreatedDate",
        "LoginType",
        "Application",
        "Browser",
        "Platform"
    ]
    
    async def get_all(self, **filters) -> List[dict]:
        """Get all login events with filters."""
        days = filters.get('days', 90)
        date_limit = datetime.utcnow() - timedelta(days=days)
        
        soql = self._build_soql(
            fields=self.QUERY_FIELDS,
            sobject="LoginEvent",
            where=f"CreatedDate >= {date_limit.strftime('%Y-%m-%dT%H:%M:%SZ')}",
            order_by="CreatedDate DESC"
        )
        
        return await self._query(soql)
    
    async def get_by_user(self, user_id: str, days: int = 90) -> List[dict]:
        """Get login events for specific user."""
        date_limit = datetime.utcnow() - timedelta(days=days)
        
        soql = self._build_soql(
            fields=self.QUERY_FIELDS,
            sobject="LoginEvent",
            where=f"UserId = '{user_id}' AND CreatedDate >= {date_limit.strftime('%Y-%m-%dT%H:%M:%SZ')}",
            order_by="CreatedDate DESC"
        )
        
        return await self._query(soql)
    
    async def get_login_counts(self, days: int = 90) -> Dict[str, int]:
        """Get login count per user."""
        events = await self.get_all(days=days)
        counts = {}
        for event in events:
            user_id = event['UserId']
            counts[user_id] = counts.get(user_id, 0) + 1
        return counts
    
    async def get_by_id(self, id: str) -> dict:
        """Not applicable for LoginEvent."""
        raise NotImplementedError()
    
    async def save(self, entity: dict) -> dict:
        """Read-only repository."""
        raise NotImplementedError("Read-only repository")

