"""Reports API — CFO action plan (JSON) and PDF download."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response

from app.api.v1.schemas import ActionPlanDTO, PlanRiskDTO, PlanStepDTO
from app.dependencies import require_tenant_match
from app.rate_limit import limiter
from app.services.analysis_service import analysis_service
from app.services.pdf_service import pdf_service
from app.services.plan_generator import plan_generator

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(require_tenant_match)])


def _plan_to_dto(plan) -> ActionPlanDTO:
    return ActionPlanDTO(
        title=plan.title,
        executive_summary=plan.executive_summary,
        steps=[PlanStepDTO(**s.model_dump()) for s in plan.steps],
        quick_wins=list(plan.quick_wins),
        risks=[PlanRiskDTO(**r.model_dump()) for r in plan.risks],
        timeline=plan.timeline,
        total_estimated_savings=plan.total_estimated_savings,
        annual_estimated_savings=plan.annual_estimated_savings,
        generated_at=plan.generated_at.isoformat(),
        model_version=plan.model_version,
    )


@router.get("/{org_id}/cfo-plan", response_model=ActionPlanDTO)
@limiter.limit("10/minute")
async def get_cfo_plan(
    request: Request,
    org_id: str,
    org_name: str = Query(default="Organization"),
):
    """Generate (or return cached) GPT-4-backed CFO action plan."""
    try:
        result = await analysis_service.get_or_run(org_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    recs = [r for recs in result.recommendations_by_user.values() for r in recs]
    plan = await plan_generator.generate(
        recommendations=recs,
        org_name=org_name,
        total_users=len(result.classified),
    )
    return _plan_to_dto(plan)


@router.get("/{org_id}/pdf")
@limiter.limit("3/minute")
async def download_pdf(
    request: Request,
    org_id: str,
    org_name: str = Query(default="Organization"),
):
    """Generate the full CFO PDF report and return it as a download."""
    try:
        result = await analysis_service.get_or_run(org_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    recs = [r for recs in result.recommendations_by_user.values() for r in recs]
    plan = await plan_generator.generate(
        recommendations=recs,
        org_name=org_name,
        total_users=len(result.classified),
    )

    try:
        pdf_bytes = pdf_service.render(result, plan, organization_name=org_name)
    except RuntimeError as exc:
        # WeasyPrint native deps missing — surface clearly instead of 500
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    filename = f"slo-report-{org_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
