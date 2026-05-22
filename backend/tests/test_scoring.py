"""
Unit tests for scoring strategies.
"""
import pytest
from decimal import Decimal
from datetime import date

from app.strategies.default_scoring import DefaultScoringStrategy
from app.models.metrics import UserMetrics


class TestDefaultScoringStrategy:
    """Test DefaultScoringStrategy."""
    
    def test_perfect_score(self):
        """Test perfect score calculation."""
        strategy = DefaultScoringStrategy()
        
        metrics = UserMetrics(
            user_id="test",
            username="test@test.com",
            license_type="Sales Cloud",
            license_cost=Decimal("150"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            last_login=date.today(),  # Today = 30 points
            login_count_90d=90,  # ~20 points
            features_used={f"feature_{i}" for i in range(80)},  # 80% = 24 points
            total_features_available=100,
            records_created=50,  # 10 points
            records_modified=50   # 10 points
        )
        
        score = strategy.calculate(metrics)
        assert score >= 80  # Should be high
        assert score <= 100
    
    def test_zero_score(self):
        """Test zero score (inactive user)."""
        strategy = DefaultScoringStrategy()
        
        metrics = UserMetrics(
            user_id="test",
            username="test@test.com",
            license_type="Sales Cloud",
            license_cost=Decimal("150"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            last_login=None,  # Never logged in
            login_count_90d=0,
            features_used=set(),
            total_features_available=100,
            records_created=0,
            records_modified=0
        )
        
        score = strategy.calculate(metrics)
        assert score == 0
    
    def test_score_breakdown(self):
        """Test score breakdown generation."""
        strategy = DefaultScoringStrategy()
        
        metrics = UserMetrics(
            user_id="test",
            username="test@test.com",
            license_type="Sales Cloud",
            license_cost=Decimal("150"),
            period_start=date(2024, 1, 1),
            period_end=date(2024, 2, 1),
            last_login=date.today(),
            login_count_90d=45,
            features_used={"Feature1", "Feature2"},
            total_features_available=100,
            records_created=10,
            records_modified=10
        )
        
        breakdown = strategy.explain(metrics)
        
        assert breakdown.last_login_score >= 0
        assert breakdown.frequency_score >= 0
        assert breakdown.features_score >= 0
        assert breakdown.records_score >= 0
        assert breakdown.last_login_explanation is not None

