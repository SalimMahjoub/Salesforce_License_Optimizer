"""Observability helpers: structured logging, request-id middleware, Sentry hook.

Sentry is *opt-in* — only initialised when ``SENTRY_DSN`` is set. The
``RequestIdMiddleware`` adds an ``X-Request-ID`` header to every response so
operators can trace logs/Sentry events to a specific HTTP call.
"""
from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter — no extra deps, structlog-compatible payload shape."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload: dict = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Promote extras
        for key, value in record.__dict__.items():
            if key in (
                "args", "msg", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "name",
            ):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(json_logs: bool = False, level: str = "INFO") -> None:
    """Install the chosen log formatter on the root logger."""
    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def init_sentry(dsn: Optional[str], environment: str) -> None:
    """Initialise Sentry SDK if a DSN is configured AND the SDK is installed."""
    if not dsn:
        return
    try:
        import sentry_sdk  # type: ignore
        from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore
        from sentry_sdk.integrations.starlette import StarletteIntegration  # type: ignore
    except ImportError:
        logger.warning("SENTRY_DSN set but sentry-sdk not installed — skipping")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=0.1,
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
    logger.info("Sentry initialised (env=%s)", environment)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach an X-Request-ID to every response and log structured access lines."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        start = time.perf_counter()
        # Make available downstream via state
        request.state.request_id = request_id
        try:
            response: Response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "elapsed_ms": round(elapsed_ms, 2),
                },
            )
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )
        return response
