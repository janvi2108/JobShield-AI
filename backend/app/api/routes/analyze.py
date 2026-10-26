"""JobShield AI ? Job Analysis and Prediction Route.

Endpoint: POST /api/analyze
Accepts job posting details and returns real ML predictions, fraud risk scoring,
heuristic threat signals, and transparent feature attributions.
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
    description="Processes job posting details through the trained champion ML pipeline to generate calibrated fraud probabilities and explainability attributions.",
)
async def analyze_job(request: JobAnalysisRequest) -> JobAnalysisResponse:
    try:
        response = analyze_job_posting(request)
        return response
    except Exception as exc:
        logger.error(f"Prediction failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while evaluating the job posting: {str(exc)}",
        )
