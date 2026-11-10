"""JobShield AI — Analyses REST API Routes.

Endpoints:
  GET    /api/analyses       - Paginated listing with search, filtering and sorting
  GET    /api/analyses/stats - Live database statistics
  GET    /api/analyses/{id}  - Full multi-table detail of a single analysis
  DELETE /api/analyses/{id}  - Cascade deletion of an analysis and dependent records
"""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status, Response

from backend.app.db.database import (
    get_analyses_list,
    get_analysis_stats,
    get_analysis_by_id,
    delete_analysis,
)

logger = logging.getLogger("jobshield.api.analyses")

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Retrieve live database aggregate statistics",
    description="Returns actual counts of total, legitimate, fraudulent, and high-risk analyses stored in SQLite.",
)
async def get_stats():
    try:
        stats = get_analysis_stats()
        return {
            "success": True,
            "data": stats,
            **stats,
        }
    except Exception as exc:
        logger.error(f"Failed to fetch analyses stats: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing database statistics: {str(exc)}",
        )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Paginated listing of analyses with search & filtering",
    description="Returns filtered and paginated analysis sessions sorted newest first.",
)
async def list_analyses(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search_title: Optional[str] = Query(default=None, description="Search by job title"),
    search_company: Optional[str] = Query(default=None, description="Search by company name"),
    classification: Optional[str] = Query(default=None, description="Filter: fraudulent or legitimate"),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk tier (CRITICAL, HIGH, MODERATE, LOW)"),
):
    try:
        items, total_count, total_pages = get_analyses_list(
            page=page,
            page_size=page_size,
            search_title=search_title,
            search_company=search_company,
            classification=classification,
            risk_level=risk_level,
        )
        return {
            "success": True,
            "analyses": items,
            "data": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
            "total_count": total_count,
            "total_pages": total_pages,
        }
    except Exception as exc:
        logger.error(f"Failed to fetch analyses list: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analyses list: {str(exc)}",
        )


@router.get(
    "/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Get full analysis record by ID",
    description="Returns complete details including extracted fields, predictions, evidence findings, and AI explanation.",
)
async def get_single_analysis(analysis_id: int):
    try:
        record = get_analysis_by_id(analysis_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis with ID {analysis_id} not found.",
            )
        return {
            "success": True,
            "analysis": record,
            "data": record,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to fetch analysis {analysis_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analysis record: {str(exc)}",
        )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an analysis and its dependent records",
    description="Deletes the analysis along with linked predictions, evidence findings, and explanations via cascading foreign keys.",
)
async def delete_single_analysis(analysis_id: int):
    try:
        deleted = delete_analysis(analysis_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis with ID {analysis_id} not found.",
            )
        return {
            "success": True,
            "message": f"Analysis {analysis_id} and all related records deleted successfully.",
            "deleted_id": analysis_id,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to delete analysis {analysis_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting analysis: {str(exc)}",
        )

