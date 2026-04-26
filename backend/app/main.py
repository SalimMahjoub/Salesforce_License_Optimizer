"""
Salesforce License Optimizer - FastAPI Application

Main entry point for the backend API.
"""
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.v1 import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Salesforce License Optimizer",
    description="Optimisation financière automatique des licences Salesforce",
    version="1.0.0",
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"CORS origins: {settings.cors_origins}")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information"""
    logger.info("Shutting down application")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns the application status and current timestamp.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app_name": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Salesforce License Optimizer API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_v1": "/api/v1"
    }

