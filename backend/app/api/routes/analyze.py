"""JobShield AI — Job Analysis and Prediction Route.

Endpoint: POST /api/analyze
Accepts job posting details and returns real ML predictions, fraud risk scoring,
heuristic threat signals, and transparent feature attributions.

Analysis results are automatically persisted to the local SQLite database.
No external API key is required for any part of this pipeline.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.analysis import JobAnalysisRequest, JobAnalysisResponse
from backend.app.services.prediction_service import analyze_job_posting

logger = logging.getLogger("jobshield.api.analyze")

router = APIRouter(tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=JobAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze job posting for potential employment fraud",
    description=(
        "Processes job posting details through the trained champion ML pipeline to generate "
        "calibrated fraud probabilities and explainability attributions. "
        "Results are stored in the local SQLite database. No external API key required."
    ),
)
async def analyze_job(request: JobAnalysisRequest) -> JobAnalysisResponse:
    try:
        response = analyze_job_posting(request)

        # Persist result to SQLite (best-effort — never blocks the API response)
        analysis_id = None
        try:
            from backend.app.db.database import save_analysis
            grounded = response.metadata.get("grounded_explanation") if response.metadata else None
            analysis_id = save_analysis(
                title=request.title,
                company=request.company_name or "",
                description=request.description,
                is_fraudulent=response.is_fraudulent,
                fraud_probability=response.fraud_probability,
                risk_level=response.risk_level,
                verdict=response.verdict,
                decision_threshold=response.decision_threshold,
                model_name=response.model_name,
                model_status=response.model_status,
                heuristic_signals=response.heuristic_signals or [],
                shap_values=response.shap_values or [],
                grounded_explanation=grounded,
                requirements=request.requirements or "",
                benefits=request.benefits or "",
                employment_type=request.employment_type or "",
                required_experience=request.required_experience or "",
                required_education=request.required_education or "",
                telecommuting=bool(request.telecommuting),
                has_company_logo=bool(request.has_company_logo),
                has_questions=bool(request.has_questions),
                source_type="manual",
                raw_input_snippet=(request.description or "")[:200],
            )
            if response.metadata is not None:
                response.metadata["analysis_id"] = analysis_id
                response.metadata["persistence_status"] = "saved"
        except Exception as db_exc:
            logger.error(f"Non-critical: failed to persist analysis to database: {db_exc}", exc_info=True)
            if response.metadata is not None:
                response.metadata["analysis_id"] = None
                response.metadata["persistence_status"] = "failed"

        return response
    except Exception as exc:
        logger.error(f"Prediction failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while evaluating the job posting: {str(exc)}",
        )
