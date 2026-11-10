"""JobShield AI — Analysis History Route.

Endpoint: GET /api/history
Returns the most recent job analysis results stored in the local SQLite database.
No external API key is required.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Query, status

logger = logging.getLogger("jobshield.api.history")

router = APIRouter(tags=["History"])


@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Retrieve analysis history from the local database",
    description="Returns recent job posting analyses stored in the local SQLite database. No external API key required.",
)
async def get_history(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    try:
        from backend.app.db.database import get_recent_analyses
        analyses = get_recent_analyses(limit=limit)
        return {
            "success": True,
            "count": len(analyses),
            "analyses": analyses,
        }
    except Exception as exc:
        logger.error(f"Failed to retrieve history: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve analysis history: {str(exc)}",
        )


@router.get(
    "/history/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Retrieve a single analysis by ID",
)
async def get_analysis(analysis_id: int) -> dict:
    try:
        from backend.app.db.database import get_analysis_by_id
        record = get_analysis_by_id(analysis_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis with id={analysis_id} not found.",
            )
        return {"success": True, "analysis": record}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to retrieve analysis {analysis_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve analysis: {str(exc)}",
        )

