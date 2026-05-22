"""Analysis API — the public surface for the dashboard.

Exposes the AnalysisService pipeline as REST endpoints:
- GET  /api/v1/analysis/{org_id}/dashboard → KPIs
- GET  /api/v1/analysis/{org_id}/zombies   → zombie users + savings
- GET  /api/v1/analysis/{org_id}/users     → paginated full user list
- POST /api/v1/analysis/{org_id}/refresh   → bust cache and recompute
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.v1.schemas import (
    ClassifiedUserDTO,
    DashboardKPIs,
    UsersListResponse,
    ZombieReport,
)
from app.dependencies import require_tenant_match
from app.models.user import UserCategory
from app.rate_limit import limiter
from app.services.analysis_service import AnalysisResult, analysis_service

# All analysis endpoints require a valid JWT whose tenant matches the URL org_id
router = APIRouter(dependencies=[Depends(require_tenant_match)])


def _to_dto(user) -> ClassifiedUserDTO:
    return ClassifiedUserDTO(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        license_type=user.license_type,
        activity_score=user.activity_score,
        category=user.category.value,
        last_login_date=user.last_login_date,
        days_inactive=user.days_inactive,
        license_cost_monthly=user.license_cost_monthly,
    )


@router.get("/{org_id}/dashboard", response_model=DashboardKPIs)
async def get_dashboard(org_id: str, days: int = Query(default=90, ge=1, le=365)):
    """Top-level KPIs powering the home dashboard."""
    try:
        result = await analysis_service.get_or_run(org_id, days=days)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}") from exc

    monthly_cost = result.total_monthly_cost()
    monthly_savings = result.total_monthly_savings()
    savings_rate = float(monthly_savings / monthly_cost) if monthly_cost > 0 else 0.0
    recs_count = sum(len(v) for v in result.recommendations_by_user.values())

    return DashboardKPIs(
        org_id=org_id,
        computed_at=result.computed_at,
        total_users=len(result.classified),
        total_monthly_cost=monthly_cost,
        total_monthly_savings=monthly_savings,
        total_annual_savings=monthly_savings * 12,
        savings_rate=round(savings_rate, 4),
        recommendations_count=recs_count,
        counts_by_category=result.counts_by_category(),
        zombie_count=len(result.zombies()),
        zombie_monthly_savings=result.zombie_savings(),
    )


@router.get("/{org_id}/zombies", response_model=ZombieReport)
async def get_zombies(org_id: str, days: int = Query(default=90, ge=1, le=365)):
    """Inactive users (UserCategory.INACTIVE) and the savings they represent."""
    result = await analysis_service.get_or_run(org_id, days=days)
    zombies = result.zombies()
    monthly_savings = result.zombie_savings()

    return ZombieReport(
        org_id=org_id,
        computed_at=result.computed_at,
        zombie_count=len(zombies),
        total_monthly_savings=monthly_savings,
        total_annual_savings=monthly_savings * 12,
        users=[_to_dto(u) for u in zombies],
    )


@router.get("/{org_id}/users", response_model=UsersListResponse)
async def list_users(
    org_id: str,
    days: int = Query(default=90, ge=1, le=365),
    category: Optional[str] = Query(default=None, description="Filter by UserCategory"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
):
    """Paginated classified user list, optionally filtered by category."""
    result = await analysis_service.get_or_run(org_id, days=days)
    users = result.classified

    if category:
        try:
            cat = UserCategory(category.lower())
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category {category!r}; "
                       f"allowed: {[c.value for c in UserCategory]}",
            ) from exc
        users = [u for u in users if u.category == cat]

    total = len(users)
    start = (page - 1) * page_size
    page_items = users[start:start + page_size]

    return UsersListResponse(
        org_id=org_id,
        total=total,
        page=page,
        page_size=page_size,
        users=[_to_dto(u) for u in page_items],
    )


@router.post("/{org_id}/refresh")
@limiter.limit("5/minute")
async def refresh(
    request: Request,
    org_id: str,
    days: int = Query(default=90, ge=1, le=365),
):
    """Force-recompute the analysis (bypasses the 5-minute cache)."""
    result = await analysis_service.get_or_run(org_id, days=days, force_refresh=True)
    return {
        "org_id": org_id,
        "computed_at": result.computed_at.isoformat(),
        "total_users": len(result.classified),
    }
