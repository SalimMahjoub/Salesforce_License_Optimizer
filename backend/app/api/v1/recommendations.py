"""
Recommendations API endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.factories.recommendation_factory import recommendation_factory
from app.services.plan_generator import plan_generator
from app.clients.gpt4_client import gpt4_client

router = APIRouter()


@router.get("/generate/{org_id}")
async def generate_recommendations(org_id: str):
    """
    Generate recommendations for organization.
    
    Args:
        org_id: Organization identifier
        
    Returns:
        Generated recommendations
    """
    try:
        # In production, fetch classified users and generate recommendations
        return {
            "success": True,
            "message": "Recommendations generated",
            "recommendations_count": 0,
            "total_monthly_savings": 0.0,
            "total_annual_savings": 0.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{org_id}")
async def list_recommendations(org_id: str):
    """
    List recommendations for organization.
    
    Args:
        org_id: Organization identifier
        
    Returns:
        List of recommendations
    """
    # Mock data
    return {
        "recommendations": [
            {
                "user_id": "005xx000001X8F3AAK",
                "username": "john.doe@company.com",
                "type": "KEEP",
                "priority": "LOW",
                "title": "Utilisation optimale - Conserver la licence",
                "monthly_savings": 0.0,
                "annual_savings": 0.0
            }
        ],
        "total": 1
    }


@router.post("/plan/{org_id}")
async def generate_action_plan(org_id: str):
    """
    Generate AI-powered action plan.
    
    Args:
        org_id: Organization identifier
        
    Returns:
        Action plan
    """
    try:
        # Initialize plan generator with GPT-4 client
        from app.services.plan_generator import PlanGenerator
        generator = PlanGenerator(gpt4_client)
        
        # In production, fetch real recommendations
        # For now, return mock
        return {
            "success": True,
            "message": "Action plan generated",
            "plan": {
                "title": "Plan d'optimisation des licences Salesforce",
                "executive_summary": "Plan d'optimisation complet...",
                "steps": []
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
