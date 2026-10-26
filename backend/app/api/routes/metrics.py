"""JobShield AI ? Model Benchmark Metrics Route.

Endpoint: GET /api/metrics
Provides real validation and test evaluation metrics, candidate comparison results,
and dataset accounting telemetry.
"""

from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from backend.app.services.prediction_service import load_metrics_data

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Get genuine candidate model comparison and test metrics",
    description="Returns the actual evaluation telemetry computed during the EMSCAD training pipeline.",
)
async def get_metrics() -> dict:
    metrics = load_metrics_data()
    if metrics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model benchmark metrics not yet generated. Run scripts/train_models.py to train and evaluate.",
        )
    return metrics
