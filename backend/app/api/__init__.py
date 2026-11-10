from fastapi import APIRouter
from .routes.health import router as health_router
from .routes.analyze import router as analyze_router
from .routes.metrics import router as metrics_router
from .routes.extract import router as extract_router
from .routes.explain import router as explain_router
from .routes.validation import router as validation_router
from .routes.history import router as history_router
from .routes.analyses import router as analyses_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analyze_router)
api_router.include_router(metrics_router)
api_router.include_router(extract_router)
api_router.include_router(explain_router)
api_router.include_router(validation_router)
api_router.include_router(history_router)
api_router.include_router(analyses_router)

__all__ = ["api_router"]
