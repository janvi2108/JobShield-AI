"""JobShield AI — Grounded Explainability Route.

Endpoint: POST /api/explain
Accepts job posting details and ML scores, returning an evidence-grounded
explanation synthesizing Linear SVM attributions, deterministic heuristic findings,
and verified applicant safety recommendations.
"""

from __future__ import annotations

import datetime
import logging
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.analysis import JobAnalysisRequest
from backend.app.schemas.explanation import ExplainRequest, ExplainResponse
from backend.app.services.llm.explanation_service import generate_grounded_explanation
from backend.app.services.prediction_service import analyze_job_posting

logger = logging.getLogger("jobshield.api.explain")

router = APIRouter(tags=["Explainability"])


@router.post(
    "/explain",
    response_model=ExplainResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate evidence-grounded AI explanation for job analysis",
    description="Synthesizes model feature attributions, deterministic threat signals, and LLM reasoning into an actionable explainability report.",
)
async def explain_job(request: ExplainRequest) -> ExplainResponse:
    try:
        # If fraud_probability is not provided, evaluate with champion ML model
        fraud_prob = request.fraud_probability
        is_fraud = request.is_fraudulent
        decision_thresh = request.decision_threshold or 0.48
        model_name = request.model_name or "Linear Support Vector Machine"
        top_fraud = []
        top_legit = []

        if fraud_prob is None or is_fraud is None:
            analysis_req = JobAnalysisRequest(
                title=request.title,
                company_name=request.company_name or "",
                description=request.description,
                requirements=request.requirements or "",
                benefits=request.benefits or "",
            )
            analysis_res = analyze_job_posting(analysis_req)
            fraud_prob = analysis_res.fraud_probability
            is_fraud = analysis_res.is_fraudulent
            decision_thresh = analysis_res.decision_threshold
            model_name = analysis_res.model_name
            if analysis_res.explanation:
                top_fraud = analysis_res.explanation.top_fraud_indicators
                top_legit = analysis_res.explanation.top_legitimate_indicators

        explanation, warnings, risk_tier = generate_grounded_explanation(
            title=request.title,
            description=request.description,
            company_name=request.company_name or "",
            requirements=request.requirements or "",
            benefits=request.benefits or "",
            fraud_probability=fraud_prob,
            is_fraudulent=is_fraud,
            decision_threshold=decision_thresh,
            model_name=model_name,
            top_fraud_features=top_fraud,
            top_legit_features=top_legit,
        )

        return ExplainResponse(
            success=True,
            is_fraudulent=is_fraud,
            fraud_probability=fraud_prob,
            risk_level=risk_tier,
            model_name=model_name,
            explanation=explanation,
            model_features=top_fraud + top_legit,
            warning_indicators=warnings,
            missing_fields=explanation.unverified_information,
            analyzed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
    except Exception as exc:
        logger.error(f"Explanation generation failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while explaining the job evaluation: {str(exc)}",
        )

