"""Salesforce repository implementations."""
from app.repositories.salesforce.base import SalesforceRepository
from app.repositories.salesforce.login_repository import LoginEventRepository
from app.repositories.salesforce.permission_repository import PermissionRepository

__all__ = [
    "SalesforceRepository",
    "LoginEventRepository",
    "PermissionRepository",
]

