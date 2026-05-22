"""
User domain models with Pydantic v2.

These models represent business entities for user classification and analysis.
The taxonomy below is the single source of truth shared by services, factories,
strategies, and tests — do not duplicate it elsewhere.
"""

from app.utils.time import utcnow
from datetime import datetime, date
from typing import Optional, List, Union
from enum import Enum
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator


class UserCategory(str, Enum):
    """
    User classification categories based on activity score (0-100).

    - INACTIVE     : 0-30   → never/rarely used, primary deactivation candidate
    - UNDERUTILIZED: 31-55  → low usage, downgrade/training candidate
    - OPTIMIZABLE  : 56-75  → good usage, fine-tune opportunities
    - EFFICIENT    : 76-100 → optimal usage, keep as-is
    """

    INACTIVE = "inactive"
    UNDERUTILIZED = "underutilized"
    OPTIMIZABLE = "optimizable"
    EFFICIENT = "efficient"

    @classmethod
    def from_score(cls, score: int) -> "UserCategory":
        if score <= 30:
            return cls.INACTIVE
        if score <= 55:
            return cls.UNDERUTILIZED
        if score <= 75:
            return cls.OPTIMIZABLE
        return cls.EFFICIENT


class SfUser(BaseModel):
    """Salesforce User as fetched from the User API."""

    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    id: str = Field(..., description="Salesforce User ID (15 or 18 chars)")
    username: str = Field(..., min_length=1)
    email: Optional[str] = None
    full_name: Optional[str] = Field(None, description="First + Last name")
    license_type: str
    profile_name: str
    last_login_date: Optional[datetime] = None
    created_date: Optional[datetime] = None
    user_type: str = "Standard"

    @field_validator("id")
    @classmethod
    def validate_sf_id(cls, v: str) -> str:
        if len(v) not in (15, 18):
            raise ValueError("Salesforce ID must be 15 or 18 characters")
        return v

    @computed_field
    @property
    def days_since_last_login(self) -> Optional[int]:
        if not self.last_login_date:
            return None
        return (utcnow() - self.last_login_date).days

    @computed_field
    @property
    def is_active(self) -> bool:
        """Active = logged in within 90 days."""
        days = self.days_since_last_login
        return days is not None and days <= 90


class ClassifiedUser(BaseModel):
    """User with classification results and scoring details."""

    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    # Identity
    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    license_type: str
    profile_name: str
    last_login_date: Optional[Union[datetime, date]] = None
    created_date: Optional[Union[datetime, date]] = None

    # Classification
    activity_score: int = Field(..., ge=0, le=100)
    category: UserCategory
    score_breakdown: Optional[object] = Field(
        default=None,
        description="ScoreBreakdown or dict — kept loose for explainability payloads",
    )

    # License cost (optional: filled when metrics are available)
    license_cost_monthly: Decimal = Field(default=Decimal("0"), ge=0)

    # Metadata
    classified_at: datetime = Field(default_factory=utcnow)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @computed_field
    @property
    def days_inactive(self) -> Optional[int]:
        if not self.last_login_date:
            return None
        last = self.last_login_date
        if isinstance(last, date) and not isinstance(last, datetime):
            last = datetime.combine(last, datetime.min.time())
        return (utcnow() - last).days

    @computed_field
    @property
    def is_inactive(self) -> bool:
        return self.category == UserCategory.INACTIVE

    @computed_field
    @property
    def is_optimization_candidate(self) -> bool:
        return self.category in (UserCategory.INACTIVE, UserCategory.UNDERUTILIZED)

    @computed_field
    @property
    def annual_license_cost(self) -> Decimal:
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
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @computed_field
    @property
    def has_previous(self) -> bool:
        return self.page > 1
