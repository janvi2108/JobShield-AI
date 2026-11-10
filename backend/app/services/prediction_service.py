"""JobShield AI — Model Prediction and Explainability Service.

Provides production inference, calibrated probability scoring, heuristic threat
detection, linear attribution / SHAP explainability, and grounded AI explanation
enrichment for incoming job postings.
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
from backend.app.services.explainability.evidence_generator import extract_evidence_findings
from backend.app.services.explainability.risk_analyzer import analyze_composite_risk_full

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
        "registration fee", "application fee", "training fee", "onboarding fee",
        "wire transfer", "moneygram", "western union", "cash app", "send money",
        "deposit required", "security deposit", "caution deposit", "crypto",
        "bitcoin", "usdt", "refundable onboarding fee", "refundable registration fee",
        "pay before joining", "account activation fee"
    ]
    if any(k in text for k in keywords_financial):
        # Contextual check: make sure not talking about company registration
        if not ("registered under" in text or "company registration" in text):
            signals.append("Financial solicitation, upfront registration fee, or onboarding deposit requested")

    # 2. Sensitive documents via informal channels
    keywords_docs = ["aadhaar", "pan card", "passport", "bank details", "bank passbook", "voter id"]
    keywords_chat = ["telegram", "whatsapp", "t.me", "wa.me", "signal messenger", "viber", "hangouts"]
    has_doc = any(d in text for d in keywords_docs)
    has_chat = any(c in text for c in keywords_chat)

    if has_doc and has_chat:
        signals.append("Sensitive identity documents (Aadhaar/PAN/Passport) requested via informal messaging (WhatsApp/Telegram)")
    elif has_chat:
        signals.append("Recruitment redirected to encrypted/external chat platform (Telegram/WhatsApp)")

    # 3. Unrealistic guarantees & bypassed hiring
    keywords_guarantee = [
        "guaranteed approval", "guaranteed income", "no interview required",
        "no experience needed", "no experience necessary", "easy money",
        "immediate hire guaranteed", "guaranteed job confirmation", "guaranteed selection",
        "guaranteed placement", "no technical interview", "no coding assessment",
        "confirmation within 24 hours"
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
    keywords_urgency = ["urgent hiring", "immediate hiring", "act now", "positions filling fast", "apply within 24 hours", "limited spots left", "limited vacancies"]
    if any(k in text for k in keywords_urgency):
        signals.append("High-pressure urgency language designed to bypass scrutiny")

    return signals


# Structural noise and stopwords to filter out from feature attribution displays
JUNK_FEATURE_TOKENS = {
    "list", "paragraph", "span", "div", "html", "item", "true", "false",
    "none", "nan", "null", "yes", "no", "ul", "li", "p", "br", "gt", "lt",
    "amp", "nbsp", "quot", "and", "or", "the", "in", "of", "to", "for", "with",
    "at", "by", "from", "on", "as", "an", "is", "it", "are", "be", "this", "that",
    "missing", "unspecified", "not specified", "other", "n/a", "na"
}

ALLOWED_SHORT_TOKENS = {"c#", "c++", "go", "r", "ui", "ux", "qa", "ml", "ai", "db", "ip"}


def normalize_feature_token(fname: str) -> Optional[str]:
    """Convert technical pipeline feature names into readable, meaningful tokens.

    Filters out:
    - Pure numeric tokens ('11', '0', '1', '2014')
    - HTML and structural artifacts ('list', 'span', 'div')
    - Raw categorical encodings into human-readable descriptions
    """
    if not fname:
        return None

    # Handle binary indicator features
    if fname.startswith("bin:"):
        bin_key = fname[4:].strip()
        mapping = {
            "has_company_logo": "Verified corporate logo",
            "has_questions": "Applicant screening questionnaire",
            "telecommuting": "Remote / telecommuting arrangement",
        }
        return mapping.get(bin_key, bin_key.replace("_", " ").title())

    # Handle categorical encoded features
    if fname.startswith("cat:"):
        cat_key = fname[4:].strip()
        # Normalization mappings for common EMSCAD categorical features
        cat_mappings = {
            "required_education_Bachelor's Degree": "Bachelor's Degree requirement",
            "required_education_Master's Degree": "Master's Degree requirement",
            "required_education_High School or equivalent": "High School education requirement",
            "required_education_Unspecified": None,
            "employment_type_Full-time": "Full-time employment structure",
            "employment_type_Part-time": "Part-time employment structure",
            "employment_type_Contract": "Contract engagement",
            "employment_type_Internship": "Internship structure",
            "employment_type_Temporary": "Temporary role",
            "employment_type_Other": None,
            "required_experience_Entry level": "Entry-level position",
            "required_experience_Mid-Senior level": "Mid-Senior experience requirement",
            "required_experience_Associate": "Associate-level experience",
            "required_experience_Director": "Director-level experience",
            "required_experience_Executive": "Executive-level experience",
            "required_experience_Not Applicable": None,
        }
        if cat_key in cat_mappings:
            return cat_mappings[cat_key]

        # General clean up for other categorical features
        clean = re.sub(r"^(required_education|employment_type|required_experience)_", "", cat_key)
        return clean.replace("_", " ").strip()

    # Handle text TF-IDF tokens
    token = fname
    if fname.startswith("text:"):
        token = fname[5:].strip()

    # Remove quotes
    token = token.strip("\"'")

    # Filter out pure numbers or digits (e.g. '11', '0', '2014', '100')
    if token.isdigit():
        return None

    # Filter out structural noise and stopwords
    low_tok = token.lower()
    if low_tok in JUNK_FEATURE_TOKENS:
        return None

    # Filter out tokens that are too short unless in allowed technical vocabulary
    if len(token) < 3 and low_tok not in ALLOWED_SHORT_TOKENS:
        return None

    return token


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

                # Normalize and clean token for human-readable display
                clean_token = normalize_feature_token(fname)
                if not clean_token:
                    continue

                contributions.append(
                    FeatureContribution(
                        token=clean_token,
                        feature_name=fname,
                        weight=round(w, 4),
                        contribution=round(contrib, 4),
                        direction="fraud_indicative" if contrib > 0 else "legitimate_indicative",
                    )
                )

        # Deduplicate contributions by token name (keeping the one with highest magnitude)
        dedup_contribs: Dict[str, FeatureContribution] = {}
        for c in contributions:
            if c.token not in dedup_contribs or abs(c.contribution) > abs(dedup_contribs[c.token].contribution):
                dedup_contribs[c.token] = c

        unique_contributions = list(dedup_contribs.values())

        # Sort positive contributions (fraud-indicative) descending
        fraud_indicative = sorted(
            [c for c in unique_contributions if c.contribution > 0],
            key=lambda x: x.contribution,
            reverse=True
        )[:top_n]

        # Sort negative contributions (legit-indicative) ascending (most negative first)
        legit_indicative = sorted(
            [c for c in unique_contributions if c.contribution < 0],
            key=lambda x: x.contribution
        )[:top_n]

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
    """Perform real ML inference, grounded evidence detection, and risk aggregation on submitted job posting."""
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

    # Transform features through pipeline
    X_sample = preprocessor.transform(input_df)

    # 1. Obtain raw calibrated probability from ML model
    probs = model.predict_proba(X_sample)[0]
    ml_fraud_prob = round(float(probs[1]), 4)

    # 2. Extract grounded evidence findings and threat heuristics
    warnings, reassuring, unverified = extract_evidence_findings(
        title=req.title,
        description=req.description,
        company_name=req.company_name or "",
        company_profile=req.company_profile or "",
        requirements=req.requirements or "",
        benefits=req.benefits or "",
    )
    heuristic_signals = extract_heuristic_signals(req)

    # 3. Transparent evidence-based risk aggregation
    risk_level, risk_basis, final_score, is_fraud = analyze_composite_risk_full(
        fraud_probability=ml_fraud_prob,
        decision_threshold=decision_threshold,
        warning_indicators=warnings,
        reassuring_indicators=reassuring,
    )

    verdict = "Potentially Fraudulent Job Posting" if is_fraud else "Likely Legitimate Employment Posting"

    # 4. Explainability attributions (filtered and normalized)
    explanation = compute_linear_attributions(X_sample, model, feature_names)

    # Flatten explanations into shap_values for frontend charts
    shap_tokens = []
    if explanation:
        for item in explanation.top_fraud_indicators:
            shap_tokens.append({"token": item.token, "value": item.contribution})
        for item in explanation.top_legitimate_indicators:
            shap_tokens.append({"token": item.token, "value": item.contribution})

    # 5. Grounded AI explanation synthesis (with deterministic fallback)
    grounded_exp_data = None
    try:
        from backend.app.services.llm.explanation_service import generate_grounded_explanation
        top_f = explanation.top_fraud_indicators if explanation else []
        top_l = explanation.top_legitimate_indicators if explanation else []
        g_exp, _, _ = generate_grounded_explanation(
            title=req.title,
            description=req.description,
            company_name=req.company_name or "",
            company_profile=req.company_profile or "",
            requirements=req.requirements or "",
            benefits=req.benefits or "",
            fraud_probability=final_score,
            is_fraudulent=is_fraud,
            risk_level=risk_level,
            decision_threshold=decision_threshold,
            model_name=model_name,
            top_fraud_features=top_f,
            top_legit_features=top_l,
            precomputed_warnings=warnings,
            precomputed_reassuring=reassuring,
            precomputed_unverified=unverified,
        )
        grounded_exp_data = g_exp.model_dump()
    except Exception as exc:
        logger.warning(f"Could not generate grounded explanation in prediction_service: {exc}", exc_info=True)

    return JobAnalysisResponse(
        success=True,
        model_status="trained",
        prediction=1 if is_fraud else 0,
        is_fraudulent=is_fraud,
        fraud_probability=final_score,
        score=final_score,
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
            "ml_fraud_probability": ml_fraud_prob,
            "evidence_adjusted_score": final_score,
            "features_evaluated": int(X_sample.shape[1]),
            "active_tokens": int(X_sample.nnz),
            "evidence_warnings_count": len(warnings),
            "evidence_reassuring_count": len(reassuring),
            "risk_scoring_basis": risk_basis,
            "grounded_explanation": grounded_exp_data,
        },
    )
