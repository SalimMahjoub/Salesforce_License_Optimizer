"""Users API (legacy).

The canonical user list now lives at ``/api/v1/analysis/{org_id}/users``
(provided by ``analysis.py``). This module is kept as a thin compatibility
shim for the Salesforce-side collection endpoint, which still has its own
use-case for ad-hoc forced refreshes from the dashboard.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_tenant_match
from app.services.collection_service import CollectionService
from app.services.oauth_service import oauth_service

router = APIRouter(dependencies=[Depends(require_tenant_match)])


@router.get("/collect/{org_id}")
async def collect_users(
    org_id: str,
    days: int = Query(default=90, ge=1, le=365),
):
    """Force a fresh Salesforce collection for the given org (sync)."""
    try:
        service = CollectionService(oauth_service)
        result = await service.collect_all(org_id, days)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "success": result.success,
        "collected_at": result.collected_at.isoformat(),
        "users_count": len(result.users),
        "login_events_count": len(result.login_events),
        "permissions_count": len(result.permissions),
        "errors": result.errors,
    }
