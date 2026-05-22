"""Authentication API: app login (JWT) and Salesforce OAuth handshake."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.dependencies import AuthContext, authenticate, get_current_context
from app.rate_limit import limiter
from app.services.oauth_service import oauth_service
from app.services.security_service import create_access_token

router = APIRouter()


class OAuthCallbackRequest(BaseModel):
    code: str
    org_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    email: str


class WhoAmI(BaseModel):
    email: str
    tenant_id: str


# --------------------------------------------------------------- App auth (JWT)
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # anti-bruteforce
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
):
    """OAuth2 password flow — accepts ``username`` + ``password`` form fields.

    The default seed user is ``demo@uprizon.io`` / ``demo-password`` (see
    ``dependencies.py``). Replace with real DB lookup in Sprint 4.
    """
    user = authenticate(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.email, tenant_id=user.tenant_id)
    return TokenResponse(
        access_token=token,
        tenant_id=user.tenant_id,
        email=user.email,
    )


@router.get("/me", response_model=WhoAmI)
async def whoami(ctx: AuthContext = Depends(get_current_context)):
    return WhoAmI(email=ctx.email, tenant_id=ctx.tenant_id)


# --------------------------------------------------------------- Salesforce OAuth
@router.get("/authorize")
async def get_authorization_url(state: str | None = None):
    """Return the Salesforce OAuth 2.0 authorization URL."""
    return {"authorization_url": oauth_service.get_authorization_url(state)}


@router.post("/callback")
async def oauth_callback(request: OAuthCallbackRequest):
    """Exchange Salesforce authorization code for tokens (server-side)."""
    try:
        token_data = await oauth_service.exchange_code_for_token(
            code=request.code, org_id=request.org_id
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "message": "Authentication successful",
        "instance_url": token_data["instance_url"],
    }
