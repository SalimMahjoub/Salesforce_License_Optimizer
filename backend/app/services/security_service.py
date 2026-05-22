"""JWT + password security primitives.

Kept intentionally small — this is the trust boundary, so we leave it
auditable in one file. Tokens are HS256 signed with ``settings.secret_key``;
passwords are hashed with bcrypt via passlib.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict

from app.config import get_settings

logger = logging.getLogger(__name__)

_ALGORITHM = "HS256"
_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8h sessions


class TokenPayload(BaseModel):
    """Decoded JWT body."""

    model_config = ConfigDict(frozen=True)

    sub: str                    # user identifier (email)
    tenant_id: str              # tenant the user belongs to
    exp: int                    # epoch seconds


def hash_password(plain: str) -> str:
    """Hash a password with bcrypt (cost 12). bcrypt truncates at 72 bytes
    by design — we enforce that limit explicitly to fail fast."""
    if len(plain.encode("utf-8")) > 72:
        raise ValueError("Passwords longer than 72 bytes are not supported")
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:  # noqa: BLE001 — corrupt hash etc.
        return False


def create_access_token(
    subject: str,
    tenant_id: str,
    expires_minutes: int = _TOKEN_EXPIRE_MINUTES,
) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> Optional[TokenPayload]:
    settings = get_settings()
    try:
        raw = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    except JWTError as exc:
        logger.info("JWT decode failed: %s", exc)
        return None
    try:
        return TokenPayload(**raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Token payload invalid: %s", exc)
        return None
