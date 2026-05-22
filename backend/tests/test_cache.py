"""In-memory cache backend tests."""
import asyncio

import pytest

from app.services.cache import InMemoryCache


@pytest.mark.asyncio
async def test_set_get_roundtrip():
    cache = InMemoryCache()
    await cache.set("k", "v", ttl_seconds=10)
    assert await cache.get("k") == "v"


@pytest.mark.asyncio
async def test_ttl_expiry():
    cache = InMemoryCache()
    await cache.set("k", "v", ttl_seconds=0)
    # 0s TTL: should expire on next get (>= comparison)
    assert await cache.get("k") is None


@pytest.mark.asyncio
async def test_miss_returns_none():
    cache = InMemoryCache()
    assert await cache.get("nope") is None
