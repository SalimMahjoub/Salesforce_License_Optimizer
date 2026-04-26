"""
Permission Set Assignment Repository.
"""
from typing import List, Dict

from app.repositories.salesforce.base import SalesforceRepository


class PermissionRepository(SalesforceRepository[dict]):
    """Repository for Permission Set Assignments."""
    
    QUERY_FIELDS = [
        "Id",
        "AssigneeId",
        "PermissionSetId",
        "PermissionSet.Name",
        "PermissionSet.Label",
        "PermissionSet.IsCustom",
        "PermissionSet.Description"
    ]
    
    async def get_all(self, **filters) -> List[dict]:
        """Get all permission set assignments."""
        soql = self._build_soql(
            fields=self.QUERY_FIELDS,
            sobject="PermissionSetAssignment"
        )
        return await self._query(soql)
    
    async def get_by_user(self, user_id: str) -> List[dict]:
        """Get permissions for specific user."""
        soql = self._build_soql(
            fields=self.QUERY_FIELDS,
            sobject="PermissionSetAssignment",
            where=f"AssigneeId = '{user_id}'"
        )
        return await self._query(soql)
    
    async def get_critical_permissions(self) -> List[dict]:
        """Get users with critical permissions."""
        critical_perms = [
            "ModifyAllData",
            "ViewAllData",
            "ManageUsers",
            "ManageInternalUsers"
        ]
        
        # This would need to query PermissionSet with specific permissions
        # Simplified for now
        return await self.get_all()
    
    async def get_by_id(self, id: str) -> dict:
        """Get by permission assignment ID."""
        soql = self._build_soql(
            fields=self.QUERY_FIELDS,
            sobject="PermissionSetAssignment",
            where=f"Id = '{id}'",
            limit=1
        )
        return await self._query_one(soql)
    
    async def save(self, entity: dict) -> dict:
        """Read-only repository."""
        raise NotImplementedError("Read-only repository")

