"""
GPT-4 Client with retry logic, caching, and streaming support.

Implements robust error handling and performance optimizations.
"""
import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator, Optional

import httpx
from openai import APIError, AsyncOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GPT4Client:
    """
    Client for OpenAI GPT-4 API with enterprise-grade features.
    
    Features:
    - Automatic retry with exponential backoff
    - Response caching (in-memory, 1 hour TTL)
    - Streaming support for long responses
    - Error handling and fallback
    - Token usage tracking
    """
    
    def __init__(self):
        """Initialize GPT-4 client."""
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.max_tokens = 2000
        self.temperature = 0.7
        
        # Initialize OpenAI async client.
        # In corporate environments with TLS inspection, the system CA bundle
        # may reject api.openai.com. Opt-in bypass via INSECURE_TLS=1 (dev only).
        if os.environ.get("INSECURE_TLS") == "1":
            logger.warning("INSECURE_TLS=1 — OpenAI client running without TLS verification")
            http_client = httpx.AsyncClient(verify=False, timeout=60.0)
            self.client = AsyncOpenAI(api_key=self.api_key, http_client=http_client)
        else:
            self.client = AsyncOpenAI(api_key=self.api_key, timeout=60.0)
        
        # Simple cache: {prompt_hash: (response, expiry)}
        self._cache: dict = {}
        self._cache_ttl = timedelta(hours=1)
        
        # Statistics
        self.total_requests = 0
        self.cache_hits = 0
        self.total_tokens_used = 0
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError))
    )
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        use_cache: bool = True
    ) -> str:
        """
        Generate completion with retry and caching.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Randomness (0-1), defaults to 0.7
            use_cache: Whether to use cache
            
        Returns:
            Generated completion text
        """
        self.total_requests += 1
        
        # Check cache
        if use_cache:
            cached = self._get_cached(prompt, system_prompt)
            if cached:
                self.cache_hits += 1
                logger.info("Cache hit for prompt")
                return cached
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Call API
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens
            
            self.total_tokens_used += tokens
            logger.info(f"GPT-4 completion: {tokens} tokens used")
            
            # Cache result
            if use_cache:
                self._set_cache(prompt, system_prompt, content)
            
            return content
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise
    
    async def complete_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> AsyncIterator[str]:
        """
        Generate completion with streaming.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Randomness (0-1)
            
        Yields:
            Text chunks as they are generated
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            raise
    
    def _get_cached(
        self,
        prompt: str,
        system_prompt: Optional[str]
    ) -> Optional[str]:
        """Get cached response if available and not expired."""
        cache_key = self._cache_key(prompt, system_prompt)
        
        if cache_key in self._cache:
            content, expiry = self._cache[cache_key]
            if datetime.now(timezone.utc).replace(tzinfo=None) < expiry:
                return content
            else:
                # Expired, remove
                del self._cache[cache_key]
        
        return None
    
    def _set_cache(
        self,
        prompt: str,
        system_prompt: Optional[str],
        content: str
    ):
        """Store response in cache with TTL."""
        cache_key = self._cache_key(prompt, system_prompt)
        expiry = datetime.now(timezone.utc).replace(tzinfo=None) + self._cache_ttl
        self._cache[cache_key] = (content, expiry)
    
    def _cache_key(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Generate cache key from prompts."""
        combined = f"{system_prompt or ''}|||{prompt}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get_stats(self) -> dict:
        """Get client statistics."""
        cache_rate = (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": f"{cache_rate:.1f}%",
            "total_tokens_used": self.total_tokens_used,
            "cached_items": len(self._cache)
        }
    
    def clear_cache(self):
        """Clear all cached responses."""
        self._cache.clear()
        logger.info("Cache cleared")


# Singleton instance
gpt4_client = GPT4Client()

