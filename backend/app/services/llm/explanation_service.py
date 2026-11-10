"""JobShield AI — Grounded Explanation Generation Service.

Orchestrates grounded explainability by synthesizing Linear SVM feature contributions,
deterministic threat heuristics, and LLM reasoning with guaranteed offline fallback.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.schemas.analysis import FeatureContribution
from backend.app.schemas.explanation import (
    ExplainResponse,
    GroundedAIExplanation,
    ReassuringIndicator,
    WarningIndicator,
)
from backend.app.services.explainability.evidence_generator import extract_evidence_findings
from backend.app.services.explainability.risk_analyzer import analyze_composite_risk
from backend.app.services.llm.groq_provider import GroqLLMProvider
from backend.app.services.llm.prompt_builder import build_explanation_prompt

logger = logging.getLogger("jobshield.llm.explanation")


def generate_deterministic_fallback_explanation(
    title: str,
    company_name: str,
    fraud_probability: float,
    is_fraudulent: bool,
    risk_level: str,
    warnings: List[WarningIndicator],
    reassuring: List[ReassuringIndicator],
    unverified: List[str],
    top_fraud_features: List[FeatureContribution],
    top_legit_features: List[FeatureContribution],
) -> GroundedAIExplanation:
    """Build a rich, structured, grounded explanation without invoking external LLMs.

    Ensures:
    - No meaningless tokens ('11', 'list', raw categorical strings).
    - Clear distinction between model statistical signals and verified facts.
    - Grounded explanations based strictly on submitted job-posting content.
    - Safety recommendations completely aligned with detected evidence.
    """
    has_critical = any(w.severity == "critical" for w in warnings)
    primary_reasons: List[str] = []

    # 1. Grounded Warning Findings (up to top 3 highest severity warnings)
    sorted_warnings = sorted(
        warnings,
        key=lambda w: 0 if w.severity == "critical" else (1 if w.severity == "high" else 2)
    )
    for w in sorted_warnings[:3]:
        evidence_snippet = w.evidence.strip()
        if len(evidence_snippet) > 80:
            evidence_snippet = evidence_snippet[:77] + "..."
        primary_reasons.append(
            f"Flagged '{w.indicator_name}' ({w.category.upper()}): {w.reason_for_flagging} [Found: \"{evidence_snippet}\"]"
        )

    # 2. Add statistical model attribution insights (only using meaningful, cleaned tokens)
    if is_fraudulent and top_fraud_features:
        clean_tokens = [f.token for f in top_fraud_features[:3] if f.token]
        if clean_tokens:
            top_tokens_str = ", ".join([f"'{t}'" for t in clean_tokens])
            primary_reasons.append(
                f"Statistical classification model detected deceptive pattern correlations associated with terms: {top_tokens_str}."
            )
    elif not is_fraudulent and top_legit_features:
        clean_tokens = [f.token for f in top_legit_features[:3] if f.token]
        if clean_tokens:
            top_tokens_str = ", ".join([f"'{t}'" for t in clean_tokens])
            primary_reasons.append(
                f"Statistical classification features align with standard recruitment terminology: {top_tokens_str}."
            )

    # 3. Add reassuring positive operational signals
    if reassuring and not has_critical:
        reassuring_names = ", ".join([r.indicator_name for r in reassuring[:2]])
        primary_reasons.append(f"Identified positive operational signals: {reassuring_names}.")

    # Fallback primary reasons if list is still empty
    if not primary_reasons:
        if is_fraudulent:
            primary_reasons.append("Job posting patterns match elevated-risk statistical indicators in the EMSCAD recruitment benchmark.")
        else:
            primary_reasons.append(
                "The submitted advertisement contains characteristics commonly found in professional recruitment postings, "
                "including a defined technical role structure, relevant educational qualifications, and specific job responsibilities. "
                "No major fraud indicators were identified in the submitted content."
            )

    # 4. Consistent Overall Summary
    pct = fraud_probability * 100.0
    if has_critical or risk_level == "CRITICAL":
        overall_summary = (
            f"The advertisement contains several critical warning signs, including advance onboarding payments, "
            f"guaranteed job confirmation without technical assessment, or requests for identity documents through informal channels "
            f"(calibrated risk: {pct:.1f}%, {risk_level} risk). These indicators warrant independent verification before sharing documents or making any payment."
        )
        verdict = "DO NOT APPLY / CRITICAL FRAUD RISK"
    elif is_fraudulent or risk_level == "HIGH":
        overall_summary = (
            f"This posting for '{title}' has been assessed as a potential employment scam with a calibrated fraud probability "
            f"of {pct:.1f}% ({risk_level} risk). Analysis identified {len(warnings)} risk signal(s) characteristic of deceptive recruitment campaigns."
        )
        verdict = "PROCEED WITH EXTREME CAUTION / VERIFICATION REQUIRED"
    elif risk_level == "MODERATE" or len(warnings) > 0:
        overall_summary = (
            f"This posting for '{title}' exhibits mixed signals or unverified recruitment details with a calibrated risk of "
            f"{pct:.1f}% ({risk_level} risk). Exercise elevated caution and verify employer authenticity through official channels."
        )
        verdict = "EXERCISE ELEVATED CAUTION / VERIFY EMPLOYER"
    else:
        overall_summary = (
            f"The submitted advertisement contains several characteristics commonly found in professional recruitment postings, "
            f"including a defined technical role, relevant educational qualifications and specific job responsibilities. "
            f"No major fraud indicators were identified in the submitted content (calibrated risk: {pct:.1f}%, {risk_level} risk)."
        )
        verdict = "PROCEED NORMALLY WITH STANDARD PROFESSIONAL CARE"

    # 5. Actionable Verification Checklist
    checklist = [
        "Verify the company exists in the official Secretary of State or corporate registry database.",
        "Check that official hiring correspondence originates from a verified company domain, never generic webmail.",
        "Ensure no upfront monetary payment, equipment fee, or financial transfer is required at any stage.",
        "Cross-reference the job opening directly on the employer's official website career portal.",
    ]
    if has_critical:
        checklist.insert(0, "Do NOT transfer any money or pay upfront registration/onboarding fees under any circumstances.")
        checklist.insert(1, "Do NOT share government identification documents (Aadhaar, PAN, Passport) or bank details over WhatsApp or unverified email.")
    elif warnings:
        checklist.insert(0, "Do NOT send personal identification documents or bank details until employment is verified through official corporate channels.")

    return GroundedAIExplanation(
        overall_summary=overall_summary,
        primary_reasons=primary_reasons,
        positive_indicators=reassuring,
        warning_signals=warnings,
        unverified_information=unverified,
        verification_checklist=checklist,
        applicant_safety_verdict=verdict,
        generation_method="deterministic_grounded_fallback",
    )


def generate_grounded_explanation(
    title: str,
    description: str,
    company_name: str = "",
    company_profile: str = "",
    requirements: str = "",
    benefits: str = "",
    fraud_probability: Optional[float] = None,
    is_fraudulent: Optional[bool] = None,
    risk_level: Optional[str] = None,
    decision_threshold: float = 0.48,
    model_name: str = "Linear Support Vector Machine",
    top_fraud_features: Optional[List[FeatureContribution]] = None,
    top_legit_features: Optional[List[FeatureContribution]] = None,
    precomputed_warnings: Optional[List[WarningIndicator]] = None,
    precomputed_reassuring: Optional[List[ReassuringIndicator]] = None,
    precomputed_unverified: Optional[List[str]] = None,
) -> Tuple[GroundedAIExplanation, List[WarningIndicator], str]:
    """Generate grounded AI explanation using Groq Cloud LLM with guaranteed offline fallback."""
    top_fraud_features = top_fraud_features or []
    top_legit_features = top_legit_features or []

    # 1. Deterministic evidence scanning (use precomputed if available to avoid duplicate work)
    if precomputed_warnings is not None:
        warnings = precomputed_warnings
        reassuring = precomputed_reassuring or []
        unverified = precomputed_unverified or []
    else:
        warnings, reassuring, unverified = extract_evidence_findings(
            title=title,
            description=description,
            company_name=company_name,
            company_profile=company_profile,
            requirements=requirements,
            benefits=benefits,
        )

    # 2. Risk tier computation if not provided
    if fraud_probability is None:
        has_critical = any(w.severity == "critical" for w in warnings)
        fraud_probability = 0.85 if has_critical else (0.55 if warnings else 0.05)
    if is_fraudulent is None:
        is_fraudulent = fraud_probability >= decision_threshold or any(w.severity == "critical" for w in warnings)
    if risk_level is None:
        risk_level, _ = analyze_composite_risk(fraud_probability, decision_threshold, warnings)

    # 3. Attempt LLM generation if provider is configured and available
    provider = GroqLLMProvider()
    if provider.is_available:
        try:
            messages = build_explanation_prompt(
                title=title,
                company_name=company_name,
                description=description,
                requirements=requirements,
                benefits=benefits,
                fraud_probability=fraud_probability,
                is_fraudulent=is_fraudulent,
                risk_level=risk_level,
                decision_threshold=decision_threshold,
                model_name=model_name,
                warnings=warnings,
                reassuring=reassuring,
                unverified=unverified,
                top_fraud_features=top_fraud_features,
                top_legit_features=top_legit_features,
            )
            raw_response = provider.generate_completion(
                messages=messages,
                temperature=0.1,
                timeout_seconds=int(settings.LLM_TIMEOUT or 30),
                response_format="json_object",
            )
            parsed = json.loads(raw_response)

            explanation = GroundedAIExplanation(
                overall_summary=parsed.get("overall_summary", ""),
                primary_reasons=parsed.get("primary_reasons", []),
                positive_indicators=[
                    ReassuringIndicator(**p) for p in parsed.get("positive_indicators", [])
                ] or reassuring,
                warning_signals=[
                    WarningIndicator(**w) for w in parsed.get("warning_signals", [])
                ] or warnings,
                unverified_information=parsed.get("unverified_information", unverified),
                verification_checklist=parsed.get("verification_checklist", []),
                applicant_safety_verdict=parsed.get("applicant_safety_verdict", "PROCEED WITH CAUTION"),
                generation_method=f"llm_{settings.LLM_PROVIDER}",
            )
            return explanation, warnings, risk_level
        except Exception as exc:
            logger.warning(f"Groq LLM explanation generation failed: {exc}. Falling back to deterministic grounded generator.")

    # 4. Deterministic fallback
    explanation = generate_deterministic_fallback_explanation(
        title=title,
        company_name=company_name,
        fraud_probability=fraud_probability,
        is_fraudulent=is_fraudulent,
        risk_level=risk_level,
        warnings=warnings,
        reassuring=reassuring,
        unverified=unverified,
        top_fraud_features=top_fraud_features,
        top_legit_features=top_legit_features,
    )
    return explanation, warnings, risk_level
