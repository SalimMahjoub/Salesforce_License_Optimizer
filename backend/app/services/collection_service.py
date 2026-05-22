"""
Collection Service orchestrating data gathering from Salesforce.

Implements Chain of Responsibility pattern for data collection pipeline.
"""
import logging
import asyncio
from decimal import Decimal
from typing import List, Dict
from datetime import datetime, date, timedelta

from app.models.license import LICENSE_CATALOG

from app.repositories.user_repository import UserRepository
from app.repositories.salesforce.login_repository import LoginEventRepository
from app.repositories.salesforce.permission_repository import PermissionRepository
from app.models.user import SfUser
from app.models.metrics import UserMetrics
from app.services.oauth_service import OAuthService
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


class CollectionResult:
    """Result of data collection process."""
    
    def __init__(self):
        self.users: List[SfUser] = []
        self.login_events: List[dict] = []
        self.permissions: List[dict] = []
        self.metrics: List[UserMetrics] = []
        self.errors: List[str] = []
        self.collected_at = utcnow()
    
    @property
    def success(self) -> bool:
        """Check if collection was successful."""
        return len(self.users) > 0 and len(self.errors) == 0


class CollectionService:
    """
    Service for orchestrating Salesforce data collection.
    
    Uses Facade pattern to simplify complex data gathering from multiple APIs.
    Implements parallel collection with asyncio.gather for performance.
    """
    
    def __init__(self, oauth_service: OAuthService):
        """
        Initialize collection service.
        
        Args:
            oauth_service: OAuth service for authentication
        """
        self.oauth_service = oauth_service
    
    async def collect_all(
        self,
        org_id: str,
        days: int = 90
    ) -> CollectionResult:
        """
        Collect all data from Salesforce APIs.
        
        Args:
            org_id: Organization identifier
            days: Number of days of historical data
            
        Returns:
            CollectionResult with all gathered data
        """
        result = CollectionResult()
        
        try:
            logger.info(f"Starting data collection for org {org_id}")
            
            # Get authenticated client
            sf_client = await self.oauth_service.get_salesforce_client(org_id)
            
            # Initialize repositories
            user_repo = UserRepository(sf_client)
            login_repo = LoginEventRepository(sf_client)
            permission_repo = PermissionRepository(sf_client)
            
            # Collect data in parallel
            users_task = user_repo.get_all()
            logins_task = login_repo.get_all(days=days)
            permissions_task = permission_repo.get_all()
            
            users, logins, permissions = await asyncio.gather(
                users_task,
                logins_task,
                permissions_task,
                return_exceptions=True
            )
            
            # Handle results
            if isinstance(users, Exception):
                result.errors.append(f"User collection failed: {str(users)}")
                logger.error(f"User collection error: {users}")
            else:
                result.users = users
                logger.info(f"Collected {len(users)} users")
            
            if isinstance(logins, Exception):
                result.errors.append(f"Login collection failed: {str(logins)}")
                logger.error(f"Login collection error: {logins}")
            else:
                result.login_events = logins
                logger.info(f"Collected {len(logins)} login events")
            
            if isinstance(permissions, Exception):
                result.errors.append(f"Permission collection failed: {str(permissions)}")
                logger.error(f"Permission collection error: {permissions}")
            else:
                result.permissions = permissions
                logger.info(f"Collected {len(permissions)} permissions")
            
            # Aggregate metrics
            if result.users and result.login_events:
                result.metrics = await self._aggregate_metrics(
                    result.users,
                    result.login_events,
                    days
                )
                logger.info(f"Generated {len(result.metrics)} user metrics")
            
            logger.info(f"Collection completed for org {org_id}")
            
        except Exception as e:
            logger.error(f"Collection failed: {e}", exc_info=True)
            result.errors.append(f"Collection failed: {str(e)}")
        
        return result
    
    async def _aggregate_metrics(
        self,
        users: List[SfUser],
        login_events: List[dict],
        days: int
    ) -> List[UserMetrics]:
        """
        Aggregate user metrics from collected data.
        
        Args:
            users: List of Salesforce users
            login_events: List of login events
            days: Time period in days
            
        Returns:
            List of UserMetrics
        """
        # Count logins per user
        login_counts = {}
        for event in login_events:
            user_id = event['UserId']
            login_counts[user_id] = login_counts.get(user_id, 0) + 1
        
        # Create metrics for each user
        metrics = []
        period_end = date.today()
        period_start = date.today() - timedelta(days=days)
        
        for user in users:
            # Get license cost
            license_info = LICENSE_CATALOG.get(
                user.license_type,
                LICENSE_CATALOG.get("Platform")
            )
            license_cost = license_info.monthly_cost if license_info else Decimal("150")
            
            metric = UserMetrics(
                user_id=user.id,
                username=user.username,
                license_type=user.license_type,
                license_cost=license_cost,
                period_start=period_start,
                period_end=period_end,
                last_login=user.last_login_date,
                login_count_90d=login_counts.get(user.id, 0),
                features_used=set(),  # Would need additional API calls
                total_features_available=100,
                records_created=0,  # Would need SetupAuditTrail data
                records_modified=0,
            )
            metrics.append(metric)
        
        return metrics


