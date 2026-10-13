from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Structured response schema for service health status."""

    status: str = Field(..., description="Overall operational health status of the service")
    service: str = Field(..., description="Name of the backend service")
    version: str = Field(..., description="Semantic version of the application")
    environment: str = Field(..., description="Current deployment environment")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of the health check invocation",
    )
    model_status: str = Field(
        ...,
        description="Lifecycle status of ML artifacts: pending_training, trained, or degraded",
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Auxiliary subsystem details such as active components",
    )

    model_config = {"protected_namespaces": ()}

