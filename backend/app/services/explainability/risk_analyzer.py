"""JobShield AI — Advanced Fraud Risk Analyzer.

Synthesizes statistical ML model probabilities, linear feature attributions,
and deterministic evidence findings into categorized risk assessments without
modifying or obscuring the underlying model score.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Union
from backend.app.schemas.explanation import WarningIndicator, ReassuringIndicator


def analyze_composite_risk_full(
    fraud_probability: float,
    decision_threshold: float,
    warning_indicators: List[WarningIndicator],
    reassuring_indicators: Optional[List[ReassuringIndicator]] = None,
) -> Tuple[str, str, float, bool]:
    """Determine composite risk tier, calculation basis, combined score, and fraud verdict.

    Combines:
    - ML statistical probability (Linear SVM baseline)
    - Grounded evidence findings (critical, high, medium indicators)
    - Reassuring operational signals

    Returns:
        (risk_tier, scoring_basis, composite_score, is_fraudulent)
    """
    reassuring = reassuring_indicators or []

    critical_warnings = [w for w in warning_indicators if w.severity == "critical"]
    high_warnings = [w for w in warning_indicators if w.severity == "high"]
    medium_warnings = [w for w in warning_indicators if w.severity == "medium"]

    has_critical = len(critical_warnings) > 0
    high_count = len(high_warnings)
    medium_count = len(medium_warnings)
    reassuring_count = len(reassuring)

    # 1. Compute transparent evidence risk adjustment
    risk_delta = 0.0

    if has_critical:
        # Critical warning (upfront fee, sensitive document extortion, untraceable wire/crypto)
        # First critical adds +0.45; subsequent criticals add +0.15
        risk_delta += 0.45 + (0.15 * (len(critical_warnings) - 1))

    if high_count > 0:
        # High warning (guaranteed job without interview, WhatsApp redirect)
        # First adds +0.18, second adds +0.10, capped at +0.32
        risk_delta += min(0.32, 0.18 + (0.10 * (high_count - 1)))

    if medium_count > 0:
        # Medium warning (free webmail, artificial urgency, unverified background)
        risk_delta += min(0.12, 0.05 * medium_count)

    # Reassuring operational signals provide negative calibration ONLY if there are no critical red flags
    if not has_critical and reassuring_count > 0:
        reassuring_discount = min(0.12, 0.04 * reassuring_count)
        risk_delta -= reassuring_discount

    # 2. Compute final composite fraud score
    composite_score = round(min(0.99, max(0.01, fraud_probability + risk_delta)), 4)

    # 3. Determine final fraud verdict
    is_fraudulent = bool(
        composite_score >= decision_threshold
        or has_critical
        or (high_count >= 2)
    )

    # 4. Categorize risk tier
    if has_critical or composite_score >= 0.75:
        tier = "CRITICAL"
        basis = (
            f"Critical employment fraud risk detected. Statistical ML base probability ({fraud_probability * 100:.1f}%) "
            f"elevated by severe textual evidence: {', '.join(w.indicator_name for w in critical_warnings[:2])}."
        )
    elif is_fraudulent or composite_score >= decision_threshold or high_count >= 2:
        tier = "HIGH"
        basis = (
            f"High scam risk. Base probability ({fraud_probability * 100:.1f}%) combined with {high_count} "
            f"high-severity warning indicator(s) exceeds decision threshold ({decision_threshold})."
        )
    elif composite_score >= 0.25 or high_count == 1 or medium_count >= 2:
        tier = "MODERATE"
        basis = (
            f"Elevated caution warranted. Composite risk score ({composite_score * 100:.1f}%) reflects mixed signals "
            f"or unverified recruitment details."
        )
    else:
        tier = "LOW"
        basis = (
            f"Low risk ({composite_score * 100:.1f}%). Submitted content aligns with standard corporate hiring "
            f"practices with {reassuring_count} reassuring operational signal(s)."
        )

    return tier, basis, composite_score, is_fraudulent


def analyze_composite_risk(
    fraud_probability: float,
    decision_threshold: float,
    warning_indicators: List[WarningIndicator],
    reassuring_indicators: Optional[List[ReassuringIndicator]] = None,
    return_full: bool = False,
) -> Union[Tuple[str, str], Tuple[str, str, float, bool]]:
    """Determine risk tier and narrative basis based on ML probability and evidence findings.

    If return_full=True, returns (risk_tier, scoring_basis, composite_score, is_fraudulent).
    If return_full=False (default), returns (risk_tier, scoring_basis) for backward compatibility.
    """
    tier, basis, score, is_fraud = analyze_composite_risk_full(
        fraud_probability=fraud_probability,
        decision_threshold=decision_threshold,
        warning_indicators=warning_indicators,
        reassuring_indicators=reassuring_indicators,
    )
    if return_full:
        return tier, basis, score, is_fraud
    return tier, basis
