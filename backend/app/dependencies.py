"""
Dependency Injection functions for FastAPI.

This module will contain:
- Database session dependencies
- Salesforce client dependencies
- Service layer dependencies
- Repository dependencies

To be implemented in Phase 2 onwards as services are created.
"""

from app.config import get_settings

# Example dependency that will be used in Phase 2+
def get_config():
    """Get application settings"""
    return get_settings()

