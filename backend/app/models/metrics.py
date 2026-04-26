"""
User metrics and usage statistics models.

These models track user activity for scoring and classification.
Includes detailed breakdown for explainability and audit trail.
"""
from datetime import date, datetime, timedelta
from typing import Optional, List, Set
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator


class UserMetrics(BaseModel):
    """
    User activity metrics for scoring algorithm.
    
    Aggregates usage data from multiple Salesforce APIs:
    - Login events (frequency, recency)
    - Feature usage (which features used)
    - Record activity (create, update operations)
    """
    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
    )

    # User identification
    user_id: str = Field(..., description="Salesforce User ID")
    username: str
    license_type: str
    license_cost: Decimal = Field(..., ge=0, description="Monthly license cost")
    
    # Time period
    period_start: date
    period_end: date
    
    # Login activity
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count_90d: int = Field(default=0, ge=0, description="Number of logins in last 90 days")
    
    # Feature usage
    features_used: Set[str] = Field(default_factory=set, description="Set of features used")
    total_features_available: int = Field(default=100, ge=0)
    
    # Record activity
    records_created: int = Field(default=0, ge=0)
    records_modified: int = Field(default=0, ge=0)
    
    # Metadata
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    
    @computed_field
    @property
    def days_since_last_login(self) -> Optional[int]:
        """Calculate days since last login."""
        if not self.last_login:
            return None
        return (datetime.utcnow() - self.last_login).days
    
    @computed_field
    @property
    def weekly_login_rate(self) -> float:
        """Calculate average logins per week over 90 days."""
        weeks = 13  # ~90 days
        return round(self.login_count_90d / weeks, 2)
    
    @computed_field
    @property
    def feature_usage_ratio(self) -> float:
        """Calculate percentage of available features used."""
        if self.total_features_available == 0:
            return 0.0
        return round(len(self.features_used) / self.total_features_available, 4)
    
    @computed_field
    @property
    def total_records_touched(self) -> int:
        """Total records created or modified."""
        return self.records_created + self.records_modified
    
    @computed_field
    @property
    def is_inactive(self) -> bool:
        """Check if user is inactive (90+ days)."""
        if not self.last_login:
            return True
        return self.days_since_last_login >= 90


class ScoreBreakdown(BaseModel):
    """
    Detailed breakdown of score calculation for explainability.
    
    Shows how each component contributes to the final score,
    enabling transparency and debugging.
    """
    model_config = ConfigDict(frozen=True)
    
    # Component scores (out of maximum points)
    last_login_score: int = Field(..., ge=0, le=30, description="Points from login recency (max 30)")
    frequency_score: int = Field(..., ge=0, le=20, description="Points from login frequency (max 20)")
    features_score: int = Field(..., ge=0, le=30, description="Points from feature usage (max 30)")
    records_score: int = Field(..., ge=0, le=20, description="Points from record activity (max 20)")
    
    # Explanations
    last_login_explanation: str = Field(..., description="Why this score for last login")
    frequency_explanation: str
    features_explanation: str
    records_explanation: str
    
    @computed_field
    @property
    def total_score(self) -> int:
        """Calculate total score from components."""
        return (
            self.last_login_score +
            self.frequency_score +
            self.features_score +
            self.records_score
        )
    
    @computed_field
    @property
    def component_weights(self) -> dict:
        """Show weight distribution of components."""
        return {
            "last_login": "30%",
            "frequency": "20%",
            "features": "30%",
            "records": "20%"
        }


class UsageStats(BaseModel):
    """
    Aggregated usage statistics for reporting.
    
    Provides summary metrics for dashboards and analytics.
    """
    model_config = ConfigDict(frozen=True)
    
    total_users: int = Field(..., ge=0)
    active_users: int = Field(..., ge=0)
    inactive_users: int = Field(..., ge=0)
    
    # By category
    zombie_count: int = Field(default=0, ge=0)
    casual_count: int = Field(default=0, ge=0)
    power_count: int = Field(default=0, ge=0)
    super_count: int = Field(default=0, ge=0)
    
    # Financial
    total_monthly_cost: Decimal = Field(..., ge=0)
    average_cost_per_user: Decimal = Field(..., ge=0)
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @computed_field
    @property
    def zombie_percentage(self) -> float:
        """Percentage of zombie users."""
        if self.total_users == 0:
            return 0.0
        return round(self.zombie_count / self.total_users * 100, 2)
    
    @computed_field
    @property
    def casual_percentage(self) -> float:
        """Percentage of casual users."""
        if self.total_users == 0:
            return 0.0
        return round(self.casual_count / self.total_users * 100, 2)
    
    @computed_field
    @property
    def power_percentage(self) -> float:
        """Percentage of power users."""
        if self.total_users == 0:
            return 0.0
        return round(self.power_count / self.total_users * 100, 2)
    
    @computed_field
    @property
    def super_percentage(self) -> float:
        """Percentage of super users."""
        if self.total_users == 0:
            return 0.0
        return round(self.super_count / self.total_users * 100, 2)
    
    @computed_field
    @property
    def activity_rate(self) -> float:
        """Percentage of active users."""
        if self.total_users == 0:
            return 0.0
        return round(self.active_users / self.total_users * 100, 2)
    
    @computed_field
    @property
    def total_annual_cost(self) -> Decimal:
        """Calculate total annual cost."""
        return self.total_monthly_cost * 12

