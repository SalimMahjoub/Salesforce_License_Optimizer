"""
Salesforce User Repository.

Retrieves user data from Salesforce User API including license information.
"""
from typing import List, Optional
from datetime import datetime

from app.repositories.salesforce.base import SalesforceRepository
from app.models.user import SfUser


class UserRepository(SalesforceRepository[SfUser]):
    """
    Repository for Salesforce User objects.
    
    Provides methods to retrieve user data with license and profile information.
    """
    
    QUERY_FIELDS = [
        "Id",
        "Username",
        "Email",
        "LastLoginDate",
        "UserType",
        "Profile.Name",
        "Profile.UserLicense.Name",
        "Profile.UserLicense.LicenseDefinitionKey",
        "IsActive"
    ]
    
    # Whitelist of accepted UserType values to prevent SOQL injection
    _ALLOWED_USER_TYPES = frozenset({
        "Standard", "PowerPartner", "PowerCustomerSuccess",
        "CustomerSuccess", "Guest", "CSPLitePortal",
    })

    async def get_all(self, **filters) -> List[SfUser]:
        """Get all active users (optionally filtered by user_type)."""
        where_clause = "IsActive = TRUE"

        user_type = filters.get("user_type")
        if user_type:
            if user_type not in self._ALLOWED_USER_TYPES:
                raise ValueError(
                    f"Invalid user_type {user_type!r}; "
                    f"allowed: {sorted(self._ALLOWED_USER_TYPES)}"
                )
            where_clause += f" AND UserType = '{user_type}'"

        soql = self._build_soql(
            fields=self.QUERY_FIELDS,
            sobject="User",
            where=where_clause,
        )
        
        records = await self._query(soql)
        return [self._to_entity(r) for r in records]
    
    async def get_by_id(self, id: str) -> Optional[SfUser]:
        """
        Get user by Salesforce ID.
        
        Args:
            id: Salesforce User ID
            
        Returns:
            SfUser or None
        """
        soql = self._build_soql(
            fields=self.QUERY_FIELDS,
            sobject="User",
            where=f"Id = '{id}'",
            limit=1,
        )
        
        record = await self._query_one(soql)
        return self._to_entity(record) if record else None
    
    async def save(self, entity: SfUser) -> SfUser:
        """Not implemented - read-only repository."""
        raise NotImplementedError("Salesforce repositories are read-only")
    
    def _to_entity(self, record: dict) -> SfUser:
        """Convert Salesforce record to SfUser."""
        return SfUser(
            id=record['Id'],
            username=record['Username'],
            email=record.get('Email'),
            license_type=record['Profile']['UserLicense']['Name'],
            profile_name=record['Profile']['Name'],
            last_login_date=self._parse_datetime(record.get('LastLoginDate')),
            user_type=record.get('UserType', 'Standard'),
        )
    
    @staticmethod
    def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        """Parse Salesforce datetime string."""
        if not date_str:
            return None
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

