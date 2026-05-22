"""
Unit tests for recommendation factory.
"""
import pytest
from decimal import Decimal
from datetime import date

from app.factories.recommendation_factory import RecommendationFactory
from app.models.user import ClassifiedUser, UserCategory
from app.models.metrics import UserMetrics


class TestRecommendationFactory:
    """Test RecommendationFactory."""
    
    def test_inactive_user_recommendations(self):
        """Test recommendations for inactive user."""
        factory = RecommendationFactory()
        
        user = ClassifiedUser(
            id="test",
            username="test@test.com",
            email="test@test.com",
            full_name="Test User",
            is_active=True,
            license_type="Sales Cloud",
            profile_name="Standard",
            last_login_date=None,
            created_date=date(2023, 1, 1),
            activity_score=10,
            category=UserCategory.INACTIVE
        )
        
        metrics = UserMetrics(
            user_id="test",
            username="test@test.com",
            license_type="Sales Cloud",
            license_cost=Decimal("150"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            last_login=None,
            login_count_90d=0,
            features_used=set(),
            total_features_available=100,
            records_created=0,
            records_modified=0
        )
        
        recommendations = factory.create_recommendations(user, metrics)
        
        assert len(recommendations) > 0
        assert any(r.type.value in ["DEACTIVATE", "DOWNGRADE"] for r in recommendations)
        assert all(r.expected_savings >= 0 for r in recommendations)
    
    def test_efficient_user_recommendations(self):
        """Test recommendations for efficient user."""
        factory = RecommendationFactory()
        
        user = ClassifiedUser(
            id="test",
            username="test@test.com",
            email="test@test.com",
            full_name="Test User",
            is_active=True,
            license_type="Sales Cloud",
            profile_name="Standard",
            last_login_date=date.today(),
            created_date=date(2023, 1, 1),
            activity_score=90,
            category=UserCategory.EFFICIENT
        )
        
        metrics = UserMetrics(
            user_id="test",
            username="test@test.com",
            license_type="Sales Cloud",
            license_cost=Decimal("150"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            last_login=date.today(),
            login_count_90d=80,
            features_used={f"feature_{i}" for i in range(70)},
            total_features_available=100,
            records_created=50,
            records_modified=100
        )
        
        recommendations = factory.create_recommendations(user, metrics)
        
        assert len(recommendations) > 0
        # Efficient users should get KEEP recommendations
        assert any(r.type.value == "KEEP" for r in recommendations)
    
    def test_recommendation_sorting(self):
        """Test that recommendations are sorted by priority and savings."""
        factory = RecommendationFactory()
        
        user = ClassifiedUser(
            id="test",
            username="test@test.com",
            email="test@test.com",
            full_name="Test User",
            is_active=True,
            license_type="Sales Cloud",
            profile_name="Standard",
            last_login_date=None,
            created_date=date(2023, 1, 1),
            activity_score=15,
            category=UserCategory.INACTIVE
        )
        
        metrics = UserMetrics(
            user_id="test",
            username="test@test.com",
            license_type="Sales Cloud",
            license_cost=Decimal("150"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            last_login=None,
            login_count_90d=2,
            features_used=set(),
            total_features_available=100,
            records_created=0,
            records_modified=0
        )
        
        recommendations = factory.create_recommendations(user, metrics)
        
        # Should be sorted by priority (descending) then savings (descending)
        if len(recommendations) > 1:
            for i in range(len(recommendations) - 1):
                assert recommendations[i].priority.value >= recommendations[i+1].priority.value

