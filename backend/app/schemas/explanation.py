"""JobShield AI — Grounded Explainability & Evidence Schemas.

Defines structured models for deterministic evidence findings, warning indicators,
linear model feature attributions, and grounded AI explanation outputs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.analysis import FeatureContribution, ShapTokenValue


class WarningIndicator(BaseModel):
    indicator_name: str
    category: str  # 'financial', 'communication', 'guarantee', 'identity', 'procedural'
    severity: str   # 'critical', 'high', 'medium', 'low', 'info'
    evidence: str   # verbatim excerpt from job posting
    reason_for_flagging: str
    source_type: str  # 'textual_evidence', 'heuristic_rule', 'missing_data'


class ReassuringIndicator(BaseModel):
    indicator_name: str
    evidence: str
    significance: str


class GroundedAIExplanation(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    overall_summary: str
    primary_reasons: List[str]
    positive_indicators: List[ReassuringIndicator]
    warning_signals: List[WarningIndicator]
    unverified_information: List[str]
    verification_checklist: List[str]
    applicant_safety_verdict: str
    generation_method: str  # 'llm_groq', 'llm_openai', or 'deterministic_grounded_fallback'


class ExplainRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    title: str
    company_name: Optional[str] = ""
    description: str
    requirements: Optional[str] = ""
    benefits: Optional[str] = ""
    fraud_probability: Optional[float] = None
    is_fraudulent: Optional[bool] = None
    decision_threshold: Optional[float] = None
    model_name: Optional[str] = None


class ExplainResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    success: bool
    is_fraudulent: bool
    fraud_probability: float
    risk_level: str
    model_name: str
    explanation: GroundedAIExplanation
    model_features: List[FeatureContribution] = Field(default_factory=list)
    warning_indicators: List[WarningIndicator] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    analyzed_at: str

