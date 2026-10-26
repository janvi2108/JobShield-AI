from fastapi import APIRouter
from .routes.health import router as health_router
from .routes.analyze import router as analyze_router
from .routes.metrics import router as metrics_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analyze_router)
api_router.include_router(metrics_router)

__all__ = ["api_router"]
