"""
Default scoring strategy implementation.

Implements standard scoring algorithm with 4 components:
- Last login recency (30 points)
- Login frequency (20 points)  
- Feature usage (30 points)
- Record activity (20 points)
"""
from datetime import datetime, timedelta

from app.strategies.base import ScoringStrategy
from app.models.metrics import UserMetrics, ScoreBreakdown


class DefaultScoringStrategy(ScoringStrategy):
    """
    Default scoring strategy for production use.
    
    Scoring breakdown:
    - Last login: 30 points (0 if >90 days, 15 if 30-90, 30 if <30)
    - Frequency: 20 points (4 points per weekly login, max 20)
    - Features: 30 points (30 * feature_usage_ratio)
    - Records: 20 points (1 point per 5 records, max 20)
    """
    
    def calculate(self, metrics: UserMetrics) -> int:
        """Calculate total score from all components."""
        score = 0
        
        # Last login component (30 points max)
        score += self._score_last_login(metrics)
        
        # Frequency component (20 points max)
        score += self._score_frequency(metrics)
        
        # Features component (30 points max)
        score += self._score_features(metrics)
        
        # Records component (20 points max)
        score += self._score_records(metrics)
        
        return min(score, 100)
    
    def explain(self, metrics: UserMetrics) -> ScoreBreakdown:
        """Generate detailed breakdown with explanations."""
        last_login_score = self._score_last_login(metrics)
        frequency_score = self._score_frequency(metrics)
        features_score = self._score_features(metrics)
        records_score = self._score_records(metrics)
        
        return ScoreBreakdown(
            last_login_score=last_login_score,
            frequency_score=frequency_score,
            features_score=features_score,
            records_score=records_score,
            last_login_explanation=self._explain_last_login(metrics, last_login_score),
            frequency_explanation=self._explain_frequency(metrics, frequency_score),
            features_explanation=self._explain_features(metrics, features_score),
            records_explanation=self._explain_records(metrics, records_score),
        )
    
    def _score_last_login(self, metrics: UserMetrics) -> int:
        """Score based on recency of last login."""
        if not metrics.last_login:
            return 0
        
        days_since = metrics.days_since_last_login
        if days_since is None:
            return 0
        
        if days_since > 90:
            return 0
        elif days_since > 30:
            return 15
        else:
            return 30
    
    def _score_frequency(self, metrics: UserMetrics) -> int:
        """Score based on login frequency."""
        weekly_rate = metrics.weekly_login_rate
        score = int(weekly_rate * 4)
        return min(score, 20)
    
    def _score_features(self, metrics: UserMetrics) -> int:
        """Score based on feature usage."""
        ratio = metrics.feature_usage_ratio
        return int(ratio * 30)
    
    def _score_records(self, metrics: UserMetrics) -> int:
        """Score based on record activity."""
        total = metrics.total_records_touched
        score = total // 5
        return min(score, 20)
    
    def _explain_last_login(self, metrics: UserMetrics, score: int) -> str:
        """Generate explanation for last login score."""
        if not metrics.last_login:
            return "Never logged in (0/30 points)"
        
        days = metrics.days_since_last_login
        if days > 90:
            return f"Inactive for {days} days (0/30 points)"
        elif days > 30:
            return f"Last login {days} days ago (15/30 points)"
        else:
            return f"Active - last login {days} days ago (30/30 points)"
    
    def _explain_frequency(self, metrics: UserMetrics, score: int) -> str:
        """Generate explanation for frequency score."""
        rate = metrics.weekly_login_rate
        return f"{rate:.1f} logins/week over 90 days ({score}/20 points)"
    
    def _explain_features(self, metrics: UserMetrics, score: int) -> str:
        """Generate explanation for features score."""
        ratio = metrics.feature_usage_ratio * 100
        count = len(metrics.features_used)
        return f"Using {count} features ({ratio:.0f}% of available) ({score}/30 points)"
    
    def _explain_records(self, metrics: UserMetrics, score: int) -> str:
        """Generate explanation for records score."""
        total = metrics.total_records_touched
        return f"{total} records created/modified ({score}/20 points)"

