"""
Classification Service for categorizing users based on activity.

Orchestrates scoring, classification, and recommendation generation.
Implements batch processing for large user bases.
"""
import logging
import asyncio
from typing import List
from datetime import datetime

from app.models.user import ClassifiedUser, UserCategory, SfUser
from app.models.metrics import UserMetrics, ScoreBreakdown
from app.models.recommendation import Recommendation
from app.strategies.base import ScoringStrategy
from app.strategies.default_scoring import DefaultScoringStrategy
from app.factories.recommendation_factory import RecommendationFactory

logger = logging.getLogger(__name__)


class ClassificationService:
    """
    Service for classifying users and generating recommendations.
    
    Implements Template Method pattern for classification workflow:
    1. Calculate activity scores
    2. Classify users into categories
    3. Generate personalized recommendations
    4. Aggregate results
    
    Supports batch processing with configurable batch sizes.
    """
    
    def __init__(
        self,
        scoring_strategy: ScoringStrategy = None,
        recommendation_factory: RecommendationFactory = None
    ):
        """
        Initialize classification service.
        
        Args:
            scoring_strategy: Strategy for calculating scores (defaults to DefaultScoringStrategy)
            recommendation_factory: Factory for generating recommendations
        """
        self.scoring_strategy = scoring_strategy or DefaultScoringStrategy()
        self.recommendation_factory = recommendation_factory or RecommendationFactory()
    
    async def classify_users(
        self,
        users: List[SfUser],
        metrics: List[UserMetrics],
        batch_size: int = 100
    ) -> List[ClassifiedUser]:
        """
        Classify a batch of users based on their metrics.
        
        Args:
            users: List of Salesforce users
            metrics: List of user metrics
            batch_size: Number of users to process per batch
            
        Returns:
            List of classified users with scores and categories
        """
        logger.info(f"Starting classification for {len(users)} users")
        start_time = datetime.utcnow()
        
        # Create metrics lookup
        metrics_map = {m.user_id: m for m in metrics}
        
        # Process in batches
        classified = []
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            batch_results = await self._process_batch(batch, metrics_map)
            classified.extend(batch_results)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(users)-1)//batch_size + 1}")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Classification completed in {duration:.2f}s")
        
        return classified
    
    async def _process_batch(
        self,
        users: List[SfUser],
        metrics_map: dict
    ) -> List[ClassifiedUser]:
        """Process a batch of users."""
        tasks = [
            self._classify_single_user(user, metrics_map.get(user.id))
            for user in users
        ]
        return await asyncio.gather(*tasks)
    
    async def _classify_single_user(
        self,
        user: SfUser,
        metrics: UserMetrics
    ) -> ClassifiedUser:
        """
        Classify a single user.
        
        Template method implementing the classification workflow:
        1. Calculate score
        2. Generate score breakdown
        3. Determine category
        4. Create classified user
        """
        if not metrics:
            # No metrics available → create default
            logger.warning(f"No metrics for user {user.id}, using defaults")
            metrics = self._create_default_metrics(user)
        
        # Step 1: Calculate score
        score = self.scoring_strategy.calculate(metrics)
        
        # Step 2: Generate breakdown
        breakdown = self.scoring_strategy.explain(metrics)
        
        # Step 3: Determine category
        category = self._categorize(score)
        
        # Step 4: Create classified user
        classified = ClassifiedUser(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            license_type=user.license_type,
            profile_name=user.profile_name,
            last_login_date=user.last_login_date,
            created_date=user.created_date,
            activity_score=score,
            category=category,
            score_breakdown=breakdown,
            classified_at=datetime.utcnow()
        )
        
        return classified
    
    def _categorize(self, score: int) -> UserCategory:
        """
        Categorize user based on activity score.
        
        Categories:
        - INACTIVE: 0-30 (never/rarely used)
        - UNDERUTILIZED: 31-55 (low usage)
        - OPTIMIZABLE: 56-75 (medium usage)
        - EFFICIENT: 76-100 (optimal usage)
        """
        if score <= 30:
            return UserCategory.INACTIVE
        elif score <= 55:
            return UserCategory.UNDERUTILIZED
        elif score <= 75:
            return UserCategory.OPTIMIZABLE
        else:
            return UserCategory.EFFICIENT
    
    def _create_default_metrics(self, user: SfUser) -> UserMetrics:
        """Create default metrics when none available."""
        from app.models.license import LICENSE_CATALOG
        from datetime import date
        from decimal import Decimal
        
        license_info = LICENSE_CATALOG.get(user.license_type)
        cost = license_info.monthly_cost if license_info else Decimal("150")
        
        return UserMetrics(
            user_id=user.id,
            username=user.username,
            license_type=user.license_type,
            license_cost=cost,
            period_start=date.today(),
            period_end=date.today(),
            last_login=user.last_login_date,
            login_count_90d=0,
            features_used=set(),
            total_features_available=100,
            records_created=0,
            records_modified=0
        )
    
    async def generate_recommendations(
        self,
        classified_users: List[ClassifiedUser],
        metrics: List[UserMetrics]
    ) -> dict:
        """
        Generate recommendations for classified users.
        
        Args:
            classified_users: List of classified users
            metrics: List of user metrics
            
        Returns:
            Dictionary mapping user_id to recommendations
        """
        logger.info(f"Generating recommendations for {len(classified_users)} users")
        
        metrics_map = {m.user_id: m for m in metrics}
        recommendations = {}
        
        for user in classified_users:
            metric = metrics_map.get(user.id)
            if metric:
                recs = self.recommendation_factory.create_recommendations(user, metric)
                recommendations[user.id] = recs
        
        total_recs = sum(len(r) for r in recommendations.values())
        logger.info(f"Generated {total_recs} recommendations")
        
        return recommendations
    
    def calculate_aggregate_savings(
        self,
        recommendations: dict
    ) -> dict:
        """
        Calculate aggregate savings potential.
        
        Args:
            recommendations: Dictionary of user_id → recommendations
            
        Returns:
            Dictionary with aggregate statistics
        """
        from decimal import Decimal
        
        total_monthly = Decimal("0")
        total_annual = Decimal("0")
        count_by_type = {}
        count_by_priority = {}
        
        for user_recs in recommendations.values():
            for rec in user_recs:
                total_monthly += rec.monthly_savings
                total_annual += rec.annual_savings
                
                count_by_type[rec.type.value] = count_by_type.get(rec.type.value, 0) + 1
                count_by_priority[rec.priority.value] = count_by_priority.get(rec.priority.value, 0) + 1
        
        return {
            "total_monthly_savings": float(total_monthly),
            "total_annual_savings": float(total_annual),
            "recommendations_by_type": count_by_type,
            "recommendations_by_priority": count_by_priority,
            "total_recommendations": sum(len(r) for r in recommendations.values())
        }


# Default instance
classification_service = ClassificationService()
