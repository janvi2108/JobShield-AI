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

    def check_llm_status(self) -> dict:
        """Report optional LLM provider configuration without requiring an API key."""
        provider = settings.LLM_PROVIDER.lower() if settings.LLM_PROVIDER else "none"
        api_key = settings.LLM_API_KEY or ""
        key_configured = bool(
            api_key.strip()
            and api_key != "your_groq_api_key_here"
            and api_key != "your_api_key_here"
        )
        if provider == "none" or not provider:
            return {
                "provider": "none",
                "status": "disabled",
                "message": "Running fully offline. Local deterministic explanation engine active.",
                "api_key_configured": False,
            }
        if key_configured:
            return {
                "provider": provider,
                "status": "configured",
                "message": f"Optional {provider.title()} AI integration is configured and available.",
                "api_key_configured": True,
            }
        return {
            "provider": provider,
            "status": "key_missing",
            "message": (
                f"LLM_PROVIDER is set to '{provider}' but no valid API key was found. "
                "The application falls back to the local deterministic explanation engine automatically."
            ),
            "api_key_configured": False,
        }

    def check_database_status(self) -> dict:
        """Verify SQLite database is accessible."""
        try:
            from ..db.database import get_connection, _get_db_path
            db_path = _get_db_path()
            conn = get_connection(db_path)
            conn.execute("SELECT 1").fetchone()
            conn.close()
            return {
                "status": "connected",
                "engine": "SQLite",
                "path": str(db_path),
            }
        except Exception as exc:
            return {
                "status": "error",
                "engine": "SQLite",
                "error": str(exc),
            }

    def get_health(self) -> HealthResponse:
        model_status, model_details = self.check_model_artifact_status()
        llm_status = self.check_llm_status()
        db_status = self.check_database_status()

        return HealthResponse(
            status="healthy",
            service="jobshield-ai-backend",
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            model_status=model_status,
            details={
                "api_prefix": settings.API_V1_PREFIX,
                "model_subsystem": model_details,
                "llm_integration": llm_status,
                "database": db_status,
            },
        )


health_service = HealthService()
