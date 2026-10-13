from fastapi import APIRouter, status
from ...schemas.health import HealthResponse
from ...services.health_service import health_service

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health and Model Subsystem Status",
    description="Returns backend operational health, configuration context, and current ML model status.",
)
async def get_health_status() -> HealthResponse:
    """Retrieve operational health and model readiness status."""
    return health_service.get_health()
