"""FastAPI dependencies — auth, tenant scoping, settings access.

Auth flow (current state, Sprint 3):
- POST /api/v1/auth/login → JWT (HS256 with SECRET_KEY)
- Bearer token decoded into ``AuthContext`` (user_email + tenant_id)
- ``get_current_context`` is the dependency every protected route uses
- ``require_tenant_match`` enforces that the path ``org_id`` matches the
  JWT's tenant_id, preventing cross-tenant data leaks via URL tampering.

In Sprint 4 the in-memory user registry below moves to PostgreSQL.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer

from app.config import get_settings
from app.services.security_service import (
    decode_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)

# tokenUrl is just metadata for OpenAPI docs (Swagger "Authorize" button)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    """The authenticated principal + their tenant scope."""

    email: str
    tenant_id: str


# ---------------------------------------------------------------------- user store
# Minimal in-memory registry seeded with one demo user.
# Replaced by SQLAlchemy queries in Sprint 4. Kept here so the auth flow is
# end-to-end testable today without a running DB.
@dataclass
class _StoredUser:
    email: str
    password_hash: str
    tenant_id: str


_DEMO_USERS: dict[str, _StoredUser] = {
    "demo@uprizon.io": _StoredUser(
        email="demo@uprizon.io",
        password_hash=hash_password("demo-password"),
        tenant_id="demo",
    ),
}


def find_user(email: str) -> Optional[_StoredUser]:
    return _DEMO_USERS.get(email.lower())


def authenticate(email: str, password: str) -> Optional[_StoredUser]:
    user = find_user(email)
    if user and verify_password(password, user.password_hash):
        return user
    return None


# ---------------------------------------------------------------------- deps
def get_config():
    return get_settings()


def get_current_context(token: Optional[str] = Depends(oauth2_scheme)) -> AuthContext:
    """Decode the Bearer token; reject with 401 if missing or invalid."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthContext(email=payload.sub, tenant_id=payload.tenant_id)


def require_tenant_match(
    org_id: str = Path(...),
    ctx: AuthContext = Depends(get_current_context),
) -> AuthContext:
    """Enforce that the URL org_id matches the JWT tenant — anti-IDOR."""
    if org_id != ctx.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch: token does not grant access to this org",
        )
    return ctx
