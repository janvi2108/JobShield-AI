from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class JobAnalysisRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=300, description="Job or internship title")
    company_name: Optional[str] = Field(default="", max_length=200, description="Employer / organization name")
    company_profile: Optional[str] = Field(default="", max_length=5000, description="Company background / profile")
    description: str = Field(..., min_length=20, max_length=50000, description="Detailed job description and requirements")
    requirements: Optional[str] = Field(default="", max_length=15000, description="Candidate qualifications / requirements")
    benefits: Optional[str] = Field(default="", max_length=10000, description="Offered benefits / compensation info")
    telecommuting: Optional[Any] = Field(default=False, description="Remote / telecommuting indicator")
    has_company_logo: Optional[Any] = Field(default=False, description="Employer logo presence")
    has_questions: Optional[Any] = Field(default=False, description="Application screening questions presence")
    employment_type: Optional[str] = Field(default="", description="Employment type (Full-time, Part-time, Contract, etc.)")
    required_experience: Optional[str] = Field(default="", description="Required experience level")
    required_education: Optional[str] = Field(default="", description="Required education level")


class FeatureContribution(BaseModel):
    token: str
    feature_name: str
    weight: float
    contribution: float
    direction: str  # 'fraud_indicative' or 'legitimate_indicative'


class ShapTokenValue(BaseModel):
    token: str
    value: float


class ExplanationSummary(BaseModel):
    method: str
    base_value: float
    top_fraud_indicators: List[FeatureContribution]
    top_legitimate_indicators: List[FeatureContribution]
    interpretation: str


class JobAnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    success: bool
    model_status: str
    prediction: int = Field(default=0, description="0 for Legitimate, 1 for Fraudulent")
    is_fraudulent: bool
    fraud_probability: float
    score: float
    verdict: str
    risk_level: str
    decision_threshold: float
    model_name: str
    heuristic_signals: List[str]
    risk_signals: List[str] = Field(default_factory=list)
    shap_values: List[ShapTokenValue] = Field(default_factory=list)
    explanation: Optional[ExplanationSummary] = None
    analyzed_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
