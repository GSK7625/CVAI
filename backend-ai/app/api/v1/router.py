"""API v1 master router aggregating all feature routers."""

from fastapi import APIRouter

from app.api.v1.career import router as career_router
from app.api.v1.cv_analysis import router as cv_router
from app.api.v1.health import router as health_router
from app.api.v1.matching import router as matching_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount endpoints
api_v1_router.include_router(health_router, prefix="")
api_v1_router.include_router(cv_router, prefix="")
api_v1_router.include_router(matching_router, prefix="")
api_v1_router.include_router(career_router, prefix="")

__all__ = ["api_v1_router"]
