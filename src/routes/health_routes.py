"""
System / health check routes.
Used by load balancers and monitoring agents.
"""

import time
from fastapi import APIRouter
from pydantic import BaseModel

from src.config import get_settings
from src.dependencies import _provider

router = APIRouter(tags=["System"])

_start_time = time.time()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    uptime_seconds: float
    ai_provider_healthy: bool


@router.get("/", include_in_schema=False)
async def root():
    settings = get_settings()
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service health status including AI provider connectivity.",
)
async def health_check() -> HealthResponse:
    settings = get_settings()
    provider = _provider()
    provider_healthy = await provider.health_check()

    return HealthResponse(
        status="healthy" if provider_healthy else "degraded",
        version=settings.app_version,
        environment=settings.app_env,
        uptime_seconds=round(time.time() - _start_time, 2),
        ai_provider_healthy=provider_healthy,
    )
