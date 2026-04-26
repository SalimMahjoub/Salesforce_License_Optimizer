"""
Recommendation models for license optimization.

Models representing optimization suggestions with ROI calculations,
risk assessment, and implementation tracking.
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator


class RecommendationType(str, Enum):
    """Types of recommendation actions (used by factory)."""
    DEACTIVATE = "DEACTIVATE"
    DOWNGRADE = "DOWNGRADE"
    KEEP = "KEEP"
    UPGRADE = "UPGRADE"
    OPTIMIZE = "OPTIMIZE"
    REVIEW = "REVIEW"


class RecommendationAction(str, Enum):
    """Types of recommendation actions."""
    DEACTIVATE = "deactivate"
    DOWNGRADE = "downgrade"
    KEEP = "keep"
    UPGRADE = "upgrade"


class Priority(str, Enum):
    """Priority levels for recommendations."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ImpactLevel(str, Enum):
    """Impact levels for recommendations."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class RiskLevel(str, Enum):
    """Risk levels for implementing recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendationStatus(str, Enum):
    """Status of recommendation implementation."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class Recommendation(BaseModel):
    """
    License optimization recommendation.
    
    Suggests specific actions to optimize license costs while
    maintaining user productivity and minimizing risks.
    """
    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
    )

    # User identification
    user_id: str
    username: str
    email: Optional[str] = None
    license_type: str = Field(..., description="Current license type")
    
    # Recommendation
    type: RecommendationType = Field(..., description="Type of recommendation")
    title: str = Field(..., description="Short title of recommendation")
    description: str = Field(..., description="Detailed description")
    rationale: List[str] = Field(default_factory=list, description="Reasoning points")
    
    # Financial impact
    expected_savings: Decimal = Field(default=Decimal("0"), ge=0)
    monthly_savings: Decimal = Field(default=Decimal("0"))
    annual_savings: Decimal = Field(default=Decimal("0"))
    
    # Priority and impact
    priority: Priority = Field(default=Priority.LOW)
    impact: ImpactLevel = Field(default=ImpactLevel.NONE)
    
    # Risk assessment
    risk_level: str = Field(default="Low")
    implementation_complexity: str = Field(default="Easy")
    implementation_time_days: int = Field(default=1, ge=0)
    
    # Approval and workflows
    requires_manager_approval: bool = Field(default=False)
    affected_workflows: List[str] = Field(default_factory=list)
    
    # Recommended state (optional)
    recommended_license: Optional[str] = Field(None, description="Recommended license type")
    recommended_cost_monthly: Optional[Decimal] = Field(None, ge=0)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: RecommendationStatus = Field(default=RecommendationStatus.PENDING)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    
    @field_validator("monthly_savings", "annual_savings")
    @classmethod
    def validate_savings(cls, v: Decimal) -> Decimal:
        """Ensure savings can be negative for upgrades."""
        return v
    
    @computed_field
    @property
    def is_cost_reduction(self) -> bool:
        """Check if recommendation reduces costs."""
        return self.monthly_savings > 0
    
    @computed_field
    @property
    def is_high_impact(self) -> bool:
        """Check if recommendation has high financial impact (>$50/month)."""
        return abs(self.monthly_savings) >= 50


class ActionPlan(BaseModel):
    """
    Comprehensive action plan with multiple recommendations.
    
    Groups recommendations by priority and provides implementation roadmap.
    """
    model_config = ConfigDict(frozen=True)
    
    # Organization info
    org_name: str
    org_id: str
    
    # Recommendations
    recommendations: List[Recommendation] = Field(default_factory=list)
    
    # Summary
    total_users_analyzed: int = Field(..., ge=0)
    total_recommendations: int = Field(..., ge=0)
    
    # Financial summary
    current_monthly_cost: Decimal = Field(..., ge=0)
    optimized_monthly_cost: Decimal = Field(..., ge=0)
    total_monthly_savings: Decimal = Field(..., ge=0)
    total_annual_savings: Decimal = Field(..., ge=0)
    
    # Timeline
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    implementation_start: Optional[datetime] = None
    implementation_end: Optional[datetime] = None
    
    @computed_field
    @property
    def savings_percentage(self) -> float:
        """Overall savings percentage."""
        if self.current_monthly_cost == 0:
            return 0.0
        return round(float(self.total_monthly_savings / self.current_monthly_cost) * 100, 2)
    
    @computed_field
    @property
    def quick_wins(self) -> List[Recommendation]:
        """Get quick win recommendations (low risk, high impact)."""
        return [
            rec for rec in self.recommendations
            if rec.risk_level.lower() in ["low", "très faible", "faible"] and rec.is_high_impact
        ][:10]
    
    @computed_field
    @property
    def high_priority_count(self) -> int:
        """Count of high priority recommendations."""
        return len([
            r for r in self.recommendations 
            if r.priority in [Priority.CRITICAL, Priority.HIGH]
        ])
    
    @computed_field
    @property
    def recommendations_by_action(self) -> dict:
        """Group recommendations by action type."""
        result = {action.value: [] for action in RecommendationType}
        for rec in self.recommendations:
            result[rec.type.value].append(rec)
        return result
    
    @computed_field
    @property
    def roi_first_year(self) -> Decimal:
        """Calculate ROI for first year (savings / implementation cost)."""
        # Assuming minimal implementation cost for license changes
        implementation_cost = Decimal("5000")  # Estimated admin time
        if implementation_cost == 0:
            return Decimal("0")
        return round((self.total_annual_savings / implementation_cost) * 100, 2)

