import os
from pathlib import Path
from ..core.config import settings
from ..schemas.health import HealthResponse


class HealthService:
    """Service responsible for aggregating system and model health status."""

    def __init__(self, models_dir: Path | None = None) -> None:
        if models_dir is None:
            # Resolve models dir relative to project root
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.models_dir = base_dir / "models"
        else:
            self.models_dir = models_dir

    def check_model_artifact_status(self) -> tuple[str, dict]:
        """Verify presence of serialized machine learning model artifacts."""
        if not self.models_dir.exists():
            return "pending_training", {"reason": "models_directory_not_found"}

        joblib_files = list(self.models_dir.glob("*.joblib"))
        pkl_files = list(self.models_dir.glob("*.pkl"))
        artifacts = [f.name for f in (joblib_files + pkl_files)]

        if artifacts:
            return "trained", {"artifacts_found": artifacts}

        return "pending_training", {
            "reason": "no_trained_model_artifacts_present",
            "candidate_models": [
                "Logistic Regression",
                "Linear SVM",
                "Random Forest",
                "XGBoost",
            ],
        }

    def get_health(self) -> HealthResponse:
        model_status, model_details = self.check_model_artifact_status()

        return HealthResponse(
            status="healthy",
            service="jobshield-ai-backend",
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            model_status=model_status,
            details={
                "api_prefix": settings.API_V1_PREFIX,
                "model_subsystem": model_details,
            },
        )


health_service = HealthService()
