"""API routes router.

Aggregates all API endpoint routers into a single main router.
"""

from fastapi import APIRouter
from .health import router as health_router
from .prediction import router as prediction_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(prediction_router)

__all__ = [
    "health_router",
    "prediction_router",
]

