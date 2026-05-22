"""Rate-limit helpers built on slowapi.

The limiter is keyed by the authenticated tenant when possible, falling back
to the client IP for unauthenticated calls. Stored in-process by default —
swap to Redis backend in production by passing ``storage_uri="redis://..."``.
"""
from __future__ import annotations

from typing import Optional

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.services.security_service import decode_access_token


def _key_func(request: Request) -> str:
    """Prefer tenant_id from the JWT, fall back to IP."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        payload = decode_access_token(token)
        if payload is not None:
            return f"tenant:{payload.tenant_id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=_key_func, default_limits=["120/minute"])
