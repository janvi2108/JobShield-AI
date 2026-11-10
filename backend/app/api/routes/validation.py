"""JobShield AI — External Dataset Validation Route.

Endpoint: GET /api/validation/external
Runs champion Linear SVM model evaluation against external / internship benchmark
datasets and provides domain generalization shift metrics.
"""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.validation import ValidationComparisonResponse
from backend.app.services.validation.evaluation import run_external_validation

logger = logging.getLogger("jobshield.api.validation")

router = APIRouter(prefix="/validation", tags=["Validation"])


@router.get(
    "/external",
    response_model=ValidationComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate champion model against external / internship scam dataset",
    description="Quantifies model generalization and domain shift across out-of-domain benchmark datasets.",
)
async def validate_external_dataset(
    file_path: Optional[str] = Query(
        default=None,
        description="Optional custom path to external dataset CSV file",
    ),
) -> ValidationComparisonResponse:
    try:
        response = run_external_validation(file_path=file_path)
        return response
    except Exception as exc:
        logger.error(f"External validation failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during external validation: {str(exc)}",
        )

