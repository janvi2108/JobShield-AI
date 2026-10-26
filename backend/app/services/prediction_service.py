"""JobShield AI ? Model Prediction and Explainability Service.

Provides production inference, calibrated probability scoring, heuristic threat
detection, and linear attribution / SHAP explainability for incoming job postings.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy import sparse

from backend.app.schemas.analysis import (
    ExplanationSummary,
    FeatureContribution,
    JobAnalysisRequest,
    JobAnalysisResponse,
)
from backend.app.services.ml_pipeline import (
    EMSCADPreprocessor,
    extract_combined_text,
    extract_binary_features,
)

logger = logging.getLogger("jobshield.prediction")

_MODEL_BUNDLE: Optional[Dict[str, Any]] = None
_METRICS_DATA: Optional[Dict[str, Any]] = None

MODEL_PATH = Path("models/model.joblib")
METRICS_PATH = Path("models/metrics.json")


def load_model_bundle(force_reload: bool = False) -> Optional[Dict[str, Any]]:
    """Load and cache the trained ML model bundle from disk."""
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is not None and not force_reload:
        return _MODEL_BUNDLE

    if not MODEL_PATH.exists():
        logger.warning(f"Model artifact not found at {MODEL_PATH}")
        return None

    try:
        _MODEL_BUNDLE = joblib.load(MODEL_PATH)
        logger.info(f"Loaded trained model: {_MODEL_BUNDLE.get('model_name')}")
        return _MODEL_BUNDLE
    except Exception as e:
        logger.error(f"Error loading model bundle from {MODEL_PATH}: {e}")
        return None


def load_metrics_data(force_reload: bool = False) -> Optional[Dict[str, Any]]:
    """Load and cache the benchmark evaluation metrics JSON from disk."""
    global _METRICS_DATA
    if _METRICS_DATA is not None and not force_reload:
        return _METRICS_DATA

    if not METRICS_PATH.exists():
        return None

    try:
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            _METRICS_DATA = json.load(f)
        return _METRICS_DATA
    except Exception as e:
        logger.error(f"Error loading metrics JSON from {METRICS_PATH}: {e}")
        return None


def extract_heuristic_signals(req: JobAnalysisRequest) -> List[str]:
    """Scan input content for known threat indicators and suspicious recruitment patterns."""
    signals = []
    text = f"{req.title} {req.company_name or ''} {req.company_profile or ''} {req.description} {req.requirements or ''} {req.benefits or ''}".lower()

    # 1. Financial / Upfront fee demands
    keywords_financial = [
        "registration fee", "application fee", "training fee", "wire transfer",
        "moneygram", "western union", "cash app", "send money", "deposit required",
        "crypto", "bitcoin", "usdt"
    ]
    if any(k in text for k in keywords_financial):
        signals.append("Financial solicitation or upfront registration/training fee requested")

    # 2. Telegram / WhatsApp / External chat recruitment
    keywords_chat = ["telegram", "whatsapp", "t.me", "wa.me", "signal messenger", "viber", "hangouts"]
    if any(k in text for k in keywords_chat):
        signals.append("Recruitment redirected to encrypted/external chat platform (Telegram/WhatsApp)")

    # 3. Unrealistic guarantees
    keywords_guarantee = [
        "guaranteed approval", "guaranteed income", "no interview required",
        "no experience needed", "no experience necessary", "easy money",
        "immediate hire guaranteed"
    ]
    if any(k in text for k in keywords_guarantee):
        signals.append("Unrealistic compensation guarantee or bypassed hiring/interview process")

    # 4. Personal communication / free webmail domains
    keywords_webmail = ["@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com"]
    if any(k in text for k in keywords_webmail):
        signals.append("Free webmail address used for official hiring inquiries instead of corporate domain")

    # 5. Missing logo / verification signals
    has_logo = str(req.has_company_logo).lower() in ["t", "true", "1"]
    if not has_logo:
        signals.append("No verified corporate employer logo present in posting")

    # 6. High urgency / artificial pressure
    keywords_urgency = ["urgent hiring", "act now", "positions filling fast", "apply within 24 hours", "limited spots left"]
    if any(k in text for k in keywords_urgency):
        signals.append("High-pressure urgency language designed to bypass scrutiny")

    return signals
def compute_linear_attributions(
    X_sample: sparse.csr_matrix,
    model: Any,
    feature_names: List[str],
    top_n: int = 6,
) -> ExplanationSummary:
    """Compute transparent linear feature attributions for the prediction."""
    try:
        # Extract weight vector from model (CalibratedClassifierCV or linear model)
        if hasattr(model, "calibrated_classifiers_"):
            # Average coefficients across CV folds
            weights = np.mean([clf.estimator.coef_.ravel() for clf in model.calibrated_classifiers_], axis=0)
            intercept = float(np.mean([clf.estimator.intercept_[0] for clf in model.calibrated_classifiers_]))
        elif hasattr(model, "coef_"):
            weights = model.coef_.ravel()
            intercept = float(model.intercept_[0]) if hasattr(model, "intercept_") else 0.0
        else:
            weights = np.zeros(len(feature_names))
            intercept = 0.0

        # Calculate instance contributions
        indices = X_sample.indices
        data = X_sample.data

        contributions = []
        for idx, val in zip(indices, data):
            if idx < len(feature_names):
                fname = feature_names[idx]
                w = float(weights[idx])
                contrib = float(w * val)
                
                # Clean token display
                clean_token = fname
                if fname.startswith("text:"):
                    clean_token = fname[5:]
                elif fname.startswith("cat:"):
                    clean_token = fname[4:]
                elif fname.startswith("bin:"):
                    clean_token = fname[4:]

                contributions.append(
                    FeatureContribution(
                        token=clean_token,
                        feature_name=fname,
                        weight=round(w, 4),
                        contribution=round(contrib, 4),
                        direction="fraud_indicative" if contrib > 0 else "legitimate_indicative",
                    )
                )

        # Sort positive contributions (fraud-indicative) descending
        fraud_indicative = sorted([c for c in contributions if c.contribution > 0], key=lambda x: x.contribution, reverse=True)[:top_n]
        # Sort negative contributions (legit-indicative) ascending
        legit_indicative = sorted([c for c in contributions if c.contribution < 0], key=lambda x: x.contribution)[:top_n]

        interp = (
            f"Classification informed by {len(fraud_indicative)} scam-correlated patterns and "
            f"{len(legit_indicative)} legitimate organizational indicators."
        )

        return ExplanationSummary(
            method="Linear Model Feature Contribution Analysis (SHAP-aligned)",
            base_value=round(float(intercept), 4),
            top_fraud_indicators=fraud_indicative,
            top_legitimate_indicators=legit_indicative,
            interpretation=interp,
        )

    except Exception as e:
        logger.error(f"Error computing attributions: {e}")
        return ExplanationSummary(
            method="Linear Model Feature Contribution Analysis",
            base_value=0.0,
            top_fraud_indicators=[],
            top_legitimate_indicators=[],
            interpretation=f"Feature attribution calculation encountered a fallback: {e}",
        )


def analyze_job_posting(req: JobAnalysisRequest) -> JobAnalysisResponse:
    """Perform real ML inference on submitted job posting."""
    bundle = load_model_bundle()

    if bundle is None:
        # Honest fallback when model artifacts are not present
        return JobAnalysisResponse(
            success=False,
            model_status="pending_training",
            is_fraudulent=False,
            fraud_probability=0.0,
            score=0.0,
            verdict="Model Awaiting Training",
            risk_level="UNKNOWN",
            decision_threshold=0.50,
            model_name="None (Awaiting Training)",
            heuristic_signals=extract_heuristic_signals(req),
            explanation=None,
            analyzed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            metadata={"message": "Candidate model artifacts are not yet loaded. Run scripts/train_models.py to train."},
        )

    model = bundle["model"]
    preprocessor: EMSCADPreprocessor = bundle["preprocessor"]
    decision_threshold = float(bundle.get("decision_threshold", 0.48))
    model_name = bundle.get("model_name", "Linear Support Vector Machine")
    feature_names = bundle.get("feature_names", [])

    # Format input row for preprocessor
    row_dict = {
        "title": req.title,
        "company_profile": req.company_profile or req.company_name or "",
        "description": req.description,
        "requirements": req.requirements or "",
        "benefits": req.benefits or "",
        "telecommuting": "1" if str(req.telecommuting).lower() in ["t", "true", "1"] else "0",
        "has_company_logo": "1" if str(req.has_company_logo).lower() in ["t", "true", "1"] else "0",
        "has_questions": "1" if str(req.has_questions).lower() in ["t", "true", "1"] else "0",
        "employment_type": req.employment_type or "missing",
        "required_experience": req.required_experience or "missing",
        "required_education": req.required_education or "missing",
    }
    input_df = pd.DataFrame([row_dict])

    # Transform features
    X_sample = preprocessor.transform(input_df)

    # Predict calibrated probability
    probs = model.predict_proba(X_sample)[0]
    fraud_prob = round(float(probs[1]), 4)
    is_fraud = bool(fraud_prob >= decision_threshold)

    # Risk level categorization
    if fraud_prob >= 0.75:
        risk_level = "CRITICAL"
    elif fraud_prob >= decision_threshold:
        risk_level = "HIGH"
    elif fraud_prob >= 0.25:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    verdict = "Potentially Fraudulent Job Posting" if is_fraud else "Likely Legitimate Employment Posting"

    # Threat heuristics
    heuristic_signals = extract_heuristic_signals(req)

    # Explainability attributions
    explanation = compute_linear_attributions(X_sample, model, feature_names)

    # Flatten explanations into shap_values for frontend charts
    shap_tokens = []
    if explanation:
        for item in explanation.top_fraud_indicators:
            shap_tokens.append({"token": item.token, "value": item.contribution})
        for item in explanation.top_legitimate_indicators:
            shap_tokens.append({"token": item.token, "value": item.contribution})

    return JobAnalysisResponse(
        success=True,
        model_status="trained",
        prediction=1 if is_fraud else 0,
        is_fraudulent=is_fraud,
        fraud_probability=fraud_prob,
        score=fraud_prob,
        verdict=verdict,
        risk_level=risk_level,
        decision_threshold=decision_threshold,
        model_name=model_name,
        heuristic_signals=heuristic_signals,
        risk_signals=heuristic_signals,
        shap_values=shap_tokens,
        explanation=explanation,
        analyzed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        metadata={
            "calibrated_scoring": True,
            "features_evaluated": int(X_sample.shape[1]),
            "active_tokens": int(X_sample.nnz),
        },
    )
