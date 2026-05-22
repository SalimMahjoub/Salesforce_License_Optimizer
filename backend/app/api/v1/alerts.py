"""Security alerts API — produced by the PermissionMonitor."""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.schemas import SecurityAlertDTO, SecurityAlertsResponse
from app.dependencies import require_tenant_match
from app.services.analysis_service import analysis_service
from app.services.permission_monitor import permission_monitor

router = APIRouter(dependencies=[Depends(require_tenant_match)])


@router.get("/{org_id}", response_model=SecurityAlertsResponse)
async def list_alerts(org_id: str):
    try:
        result = await analysis_service.get_or_run(org_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    alerts = permission_monitor.scan(result)
    counts = Counter(a.severity for a in alerts)
    return SecurityAlertsResponse(
        org_id=org_id,
        total=len(alerts),
        by_severity=dict(counts),
        alerts=[
            SecurityAlertDTO(
                user_id=a.user_id,
                username=a.username,
                severity=a.severity,
                permission=a.permission,
                description=a.description,
                recommended_action=a.recommended_action,
            )
            for a in alerts
        ],
    )
