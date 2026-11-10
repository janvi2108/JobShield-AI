"""JobShield AI — Extraction API Routes.

Endpoints:
- POST /api/extract/url: Safe extraction from public web posting URL
- POST /api/extract/text: Extraction from raw pasted posting text
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.extraction import (
    UrlExtractionRequest,
    TextExtractionRequest,
    ExtractionResponse,
)
from backend.app.services.extraction import extraction_service

logger = logging.getLogger("jobshield.api.extract")

router = APIRouter(prefix="/extract", tags=["Extraction"])


@router.post(
    "/url",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured job information from a posting URL",
    description="Fetches public job webpage safely with SSRF protection and extracts structured recruitment attributes.",
)
async def extract_url(request: UrlExtractionRequest) -> ExtractionResponse:
    try:
        response = extraction_service.extract_from_url(request)
        return response
    except Exception as exc:
        logger.error(f"Unexpected error during URL extraction: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract job posting from URL. Please verify the link or paste the text directly.",
        )


@router.post(
    "/text",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured job information from pasted text",
    description="Parses unstructured job post or copied internship announcement into normalized structured fields.",
)
async def extract_text(request: TextExtractionRequest) -> ExtractionResponse:
    try:
        response = extraction_service.extract_from_text(request)
        return response
    except ValueError as exc:
        logger.warning(f"Validation failure for text extraction: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error during text extraction: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract structured fields from text. Please check the text format.",
        )
