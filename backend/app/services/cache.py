"""Pluggable cache backend.

Uses redis.asyncio if ``REDIS_URL`` is reachable, otherwise falls back to an
in-process dict with TTL. The Redis path is exercised in production; the
in-memory fallback lets tests run with no infra.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Optional, Protocol

from app.config import get_settings
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


class Cache(Protocol):
    async def get(self, key: str) -> Optional[str]: ...
    async def set(self, key: str, value: str, ttl_seconds: int) -> None: ...


class InMemoryCache:
    def __init__(self) -> None:
        self._data: dict[str, tuple[str, datetime]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if utcnow() >= expiry:
                self._data.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        async with self._lock:
            self._data[key] = (value, utcnow() + timedelta(seconds=ttl_seconds))


class RedisCache:
    def __init__(self, url: str):
        # Lazy import so the module is loadable without redis installed
        import redis.asyncio as redis  # type: ignore

        self._client = redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        try:
            return await self._client.get(key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis GET failed (%s) — treating as miss", exc)
            return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        try:
            await self._client.set(key, value, ex=ttl_seconds)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis SET failed (%s) — value not cached", exc)


_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """Return the singleton cache, picking Redis if configured."""
    global _cache
    if _cache is not None:
        return _cache

    settings = get_settings()
    if settings.redis_url:
        try:
            _cache = RedisCache(settings.redis_url)
            logger.info("Cache backend = Redis (%s)", settings.redis_url)
            return _cache
        except Exception as exc:  # noqa: BLE001 — redis missing or unreachable
            logger.warning("Redis backend unavailable (%s) — using in-memory cache", exc)

    _cache = InMemoryCache()
    logger.info("Cache backend = in-memory")
    return _cache


def reset_cache_for_tests() -> None:
    """Force re-resolution of the cache backend (used by tests)."""
    global _cache
    _cache = None
