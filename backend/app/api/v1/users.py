"""
Users API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List

from app.services.collection_service import CollectionService
from app.services.classification_service import classification_service
from app.services.oauth_service import oauth_service

router = APIRouter()


@router.get("/collect/{org_id}")
async def collect_users(
    org_id: str,
    days: int = Query(default=90, ge=1, le=365)
):
    """
    Collect user data from Salesforce.
    
    Args:
        org_id: Organization identifier
        days: Number of days of historical data
        
    Returns:
        Collection results
    """
    try:
        collection_service = CollectionService(oauth_service)
        result = await collection_service.collect_all(org_id, days)
        
        return {
            "success": result.success,
            "collected_at": result.collected_at.isoformat(),
            "users_count": len(result.users),
            "login_events_count": len(result.login_events),
            "permissions_count": len(result.permissions),
            "errors": result.errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify/{org_id}")
async def classify_users(org_id: str):
    """
    Classify collected users.
    
    Args:
        org_id: Organization identifier
        
    Returns:
        Classification results
    """
    try:
        # In production, fetch from database
        # For now, return mock response
        return {
            "success": True,
            "message": "Classification completed",
            "users_classified": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{org_id}")
async def list_users(org_id: str):
    """
    List classified users for organization.
    
    Args:
        org_id: Organization identifier
        
    Returns:
        List of users
    """
    # Mock data for demo
    return {
        "users": [
            {
                "id": "005xx000001X8F3AAK",
                "username": "john.doe@company.com",
                "email": "john.doe@company.com",
                "license_type": "Sales Cloud",
                "activity_score": 85,
                "category": "EFFICIENT",
                "last_login_date": "2024-02-08T10:30:00Z"
            }
        ],
        "total": 1
    }

