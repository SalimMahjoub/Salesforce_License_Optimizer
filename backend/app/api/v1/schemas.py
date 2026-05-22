"""API response schemas (DTOs) — separate from domain models.

Domain models keep their internal shape; API schemas are the public contract
that the frontend depends on, so we can evolve internals without breaking
clients.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ClassifiedUserDTO(BaseModel):
    """User row as exposed to the dashboard."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    license_type: str
    activity_score: int
    category: str
    last_login_date: Optional[datetime] = None
    days_inactive: Optional[int] = None
    license_cost_monthly: Decimal


class DashboardKPIs(BaseModel):
    org_id: str
    computed_at: datetime
    total_users: int
    total_monthly_cost: Decimal
    total_monthly_savings: Decimal
    total_annual_savings: Decimal
    savings_rate: float = Field(..., description="Savings / current cost, 0..1")
    recommendations_count: int
    counts_by_category: dict
    zombie_count: int
    zombie_monthly_savings: Decimal


class ZombieReport(BaseModel):
    org_id: str
    computed_at: datetime
    zombie_count: int
    total_monthly_savings: Decimal
    total_annual_savings: Decimal
    users: List[ClassifiedUserDTO]


class UsersListResponse(BaseModel):
    org_id: str
    total: int
    page: int
    page_size: int
    users: List[ClassifiedUserDTO]


class RecommendationDTO(BaseModel):
    user_id: str
    username: str
    license_type: str
    type: str
    title: str
    description: str
    rationale: List[str]
    priority: str
    impact: str
    monthly_savings: Decimal
    annual_savings: Decimal
    risk_level: str
    implementation_complexity: str
    implementation_time_days: int


class RecommendationsListResponse(BaseModel):
    org_id: str
    total: int
    total_monthly_savings: Decimal
    total_annual_savings: Decimal
    page: int
    page_size: int
    recommendations: List[RecommendationDTO]


class PlanStepDTO(BaseModel):
    title: str
    description: str
    duration_days: int
    resources: List[str]
    success_criteria: List[str]


class PlanRiskDTO(BaseModel):
    risk: str
    mitigation: str


class SecurityAlertDTO(BaseModel):
    user_id: str
    username: str
    severity: str
    permission: str
    description: str
    recommended_action: str


class SecurityAlertsResponse(BaseModel):
    org_id: str
    total: int
    by_severity: dict
    alerts: List[SecurityAlertDTO]


class ActionPlanDTO(BaseModel):
    title: str
    executive_summary: str
    steps: List[PlanStepDTO]
    quick_wins: List[str]
    risks: List[PlanRiskDTO]
    timeline: str
    total_estimated_savings: Decimal
    annual_estimated_savings: Decimal
    generated_at: Optional[str] = None
    model_version: Optional[str] = None
