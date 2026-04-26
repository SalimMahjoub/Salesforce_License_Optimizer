"""
User domain models with Pydantic v2.

These models represent business entities for user classification and analysis.
All models use strict validation and provide computed properties for business logic.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator


class UserCategory(str, Enum):
    """
    User classification categories based on activity level.
    
    Categories are determined by scoring algorithm (0-100):
    - ZOMBIE: 0-10 (inactive 90+ days)
    - CASUAL: 11-30 (sporadic usage)
    - POWER: 31-70 (regular usage)
    - SUPER: 71-100 (intensive usage)
    """
    ZOMBIE = "zombie"
    CASUAL = "casual"
    POWER = "power"
    SUPER = "super"

    @classmethod
    def from_score(cls, score: int) -> "UserCategory":
        """
        Determine category from score.
        
        Args:
            score: User activity score (0-100)
            
        Returns:
            UserCategory enum value
        """
        if score <= 10:
            return cls.ZOMBIE
        elif score <= 30:
            return cls.CASUAL
        elif score <= 70:
            return cls.POWER
        else:
            return cls.SUPER


class SfUser(BaseModel):
    """
    Salesforce User model from User API.
    
    Represents a user in the Salesforce org with their current license
    and basic information needed for analysis.
    """
    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    id: str = Field(..., description="Salesforce User ID (18 chars)")
    username: str = Field(..., min_length=1, description="Username/email")
    email: Optional[str] = Field(None, description="Email address")
    license_type: str = Field(..., description="Current license type")
    profile_name: str = Field(..., description="Salesforce profile name")
    last_login_date: Optional[datetime] = Field(None, description="Last login timestamp")
    user_type: str = Field(default="Standard", description="User type (Standard, etc.)")
    
    @field_validator("id")
    @classmethod
    def validate_sf_id(cls, v: str) -> str:
        """Validate Salesforce ID format (18 characters)."""
        if len(v) not in [15, 18]:
            raise ValueError("Salesforce ID must be 15 or 18 characters")
        return v
    
    @computed_field
    @property
    def days_since_last_login(self) -> Optional[int]:
        """Calculate days since last login."""
        if not self.last_login_date:
            return None
        delta = datetime.utcnow() - self.last_login_date
        return delta.days
    
    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if user is considered active (logged in within 90 days)."""
        if not self.last_login_date:
            return False
        return self.days_since_last_login <= 90


class ClassifiedUser(BaseModel):
    """
    User with classification results and scoring details.
    
    Extends SfUser with computed score, category, and explainability data.
    Used after running classification algorithm.
    """
    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
    )

    # Basic user info
    id: str
    username: str
    email: Optional[str] = None
    license_type: str
    profile_name: str
    last_login_date: Optional[datetime] = None
    
    # Classification results
    score: int = Field(..., ge=0, le=100, description="Activity score (0-100)")
    category: UserCategory = Field(..., description="Classification category")
    
    # License cost
    license_cost_monthly: Decimal = Field(..., ge=0, description="Current monthly license cost")
    
    # Score breakdown for explainability
    score_breakdown: dict = Field(
        default_factory=dict,
        description="Detailed score calculation by component"
    )
    
    # Metadata
    classified_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    @computed_field
    @property
    def days_inactive(self) -> Optional[int]:
        """Days since last login."""
        if not self.last_login_date:
            return None
        return (datetime.utcnow() - self.last_login_date).days
    
    @computed_field
    @property
    def is_zombie(self) -> bool:
        """Check if user is classified as zombie."""
        return self.category == UserCategory.ZOMBIE
    
    @computed_field
    @property
    def is_optimization_candidate(self) -> bool:
        """Check if user is candidate for optimization (zombie or casual)."""
        return self.category in [UserCategory.ZOMBIE, UserCategory.CASUAL]
    
    @computed_field
    @property
    def annual_license_cost(self) -> Decimal:
        """Calculate annual license cost."""
        return self.license_cost_monthly * 12


class UserListResponse(BaseModel):
    """Response model for paginated user lists."""
    model_config = ConfigDict(frozen=True)
    
    users: List[ClassifiedUser] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=1000)
    
    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
    
    @computed_field
    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return self.page < self.total_pages
    
    @computed_field
    @property
    def has_previous(self) -> bool:
        """Check if there are previous pages."""
        return self.page > 1

