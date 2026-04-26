"""
Authentication API endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.oauth_service import oauth_service

router = APIRouter()


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request model."""
    code: str
    org_id: str


@router.get("/authorize")
async def get_authorization_url(state: str = None):
    """
    Get Salesforce OAuth authorization URL.
    
    Args:
        state: Optional state parameter for CSRF protection
        
    Returns:
        Authorization URL
    """
    url = oauth_service.get_authorization_url(state)
    return {"authorization_url": url}


@router.post("/callback")
async def oauth_callback(request: OAuthCallbackRequest):
    """
    Handle OAuth callback and exchange code for token.
    
    Args:
        request: OAuth callback request
        
    Returns:
        Token data
    """
    try:
        token_data = await oauth_service.exchange_code_for_token(
            code=request.code,
            org_id=request.org_id
        )
        return {
            "success": True,
            "message": "Authentication successful",
            "instance_url": token_data["instance_url"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

