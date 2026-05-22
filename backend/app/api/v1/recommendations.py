"""Recommendations API — list aggregated recommendations per org."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.schemas import RecommendationDTO, RecommendationsListResponse
from app.dependencies import require_tenant_match
from app.services.analysis_service import analysis_service

router = APIRouter(dependencies=[Depends(require_tenant_match)])


def _to_dto(rec) -> RecommendationDTO:
    return RecommendationDTO(
        user_id=rec.user_id,
        username=rec.username,
        license_type=rec.license_type,
        type=rec.type.value,
        title=rec.title,
        description=rec.description,
        rationale=list(rec.rationale),
        priority=rec.priority.value,
        impact=rec.impact.value,
        monthly_savings=rec.monthly_savings,
        annual_savings=rec.annual_savings,
        risk_level=rec.risk_level,
        implementation_complexity=rec.implementation_complexity,
        implementation_time_days=rec.implementation_time_days,
    )


@router.get("/{org_id}", response_model=RecommendationsListResponse)
async def list_recommendations(
    org_id: str,
    priority: Optional[str] = Query(default=None, description="CRITICAL|HIGH|MEDIUM|LOW"),
    type: Optional[str] = Query(default=None, description="DEACTIVATE|DOWNGRADE|KEEP|UPGRADE|OPTIMIZE|REVIEW"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
):
    """Aggregated, sortable recommendations for the org (priority desc, savings desc)."""
    try:
        result = await analysis_service.get_or_run(org_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    flat = [r for recs in result.recommendations_by_user.values() for r in recs]

    if priority:
        priority_upper = priority.upper()
        flat = [r for r in flat if r.priority.value == priority_upper]
    if type:
        type_upper = type.upper()
        flat = [r for r in flat if r.type.value == type_upper]

    # Stable sort: priority CRITICAL > HIGH > MEDIUM > LOW, then monthly savings desc
    priority_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    flat.sort(key=lambda r: (priority_rank.get(r.priority.value, 99), -float(r.monthly_savings)))

    total = len(flat)
    start = (page - 1) * page_size
    page_items = flat[start:start + page_size]

    # Rollup: max savings per user to avoid double-counting overlapping recos
    by_user: dict[str, Decimal] = {}
    by_user_annual: dict[str, Decimal] = {}
    for r in flat:
        if r.monthly_savings > by_user.get(r.user_id, Decimal("0")):
            by_user[r.user_id] = r.monthly_savings
            by_user_annual[r.user_id] = r.annual_savings
    realistic_monthly = sum(by_user.values(), Decimal("0"))
    realistic_annual = sum(by_user_annual.values(), Decimal("0"))

    return RecommendationsListResponse(
        org_id=org_id,
        total=total,
        total_monthly_savings=realistic_monthly,
        total_annual_savings=realistic_annual,
        page=page,
        page_size=page_size,
        recommendations=[_to_dto(r) for r in page_items],
    )
