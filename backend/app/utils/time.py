"""Centralised time helpers.

``datetime.utcnow()`` is deprecated in Python 3.12+ and returns a naive
datetime, which is a footgun. We expose a single helper that returns naive
UTC (to keep parity with existing Pydantic models that don't carry tz info)
while internally going through the timezone-aware ``datetime.now(timezone.utc)``.

Migration target: make models timezone-aware in a future sprint.
"""
from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current UTC time, naive (tzinfo stripped)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utcnow_aware() -> datetime:
    """Return current UTC time, timezone-aware (preferred for new code)."""
    return datetime.now(timezone.utc)
