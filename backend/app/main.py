"""Salesforce License Optimizer - FastAPI Application

Main entry point for the backend API.
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import get_settings
from app.observability import RequestIdMiddleware, configure_logging, init_sentry
from app.rate_limit import limiter

settings = get_settings()
configure_logging(json_logs=settings.json_logs, level=settings.log_level)
init_sentry(settings.sentry_dsn, settings.app_env)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup + shutdown hooks (replaces on_event)."""
    logger.info(
        "startup",
        extra={
            "app_name": settings.app_name,
            "env": settings.app_env,
            "debug": settings.debug,
            "data_provider": settings.data_provider,
            "json_logs": settings.json_logs,
        },
    )
    yield
    logger.info("shutdown")


app = FastAPI(
    title="Salesforce License Optimizer",
    description="Optimisation financière automatique des licences Salesforce",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Rate limiting: slowapi attaches a 429 handler and exposes the limiter via app.state
app.state.limiter = limiter
from slowapi import _rate_limit_exceeded_handler  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app_name": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Salesforce License Optimizer API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_v1": "/api/v1",
    }
