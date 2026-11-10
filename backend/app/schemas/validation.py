"""JobShield AI — External Dataset Validation Schemas.

Defines data contracts for benchmarking the champion ML model against independent
external datasets (e.g. Internship Job Scam Dataset) to quantify out-of-domain generalization.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ConfusionMatrix(BaseModel):
    true_negative: int
    false_positive: int
    false_negative: int
    true_positive: int


class DatasetMetricSummary(BaseModel):
    dataset_name: str
    sample_count: int
    fraud_count: int
    legitimate_count: int
    fraud_prevalence: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    pr_auc: Optional[float] = None
    roc_auc: Optional[float] = None
    confusion_matrix: ConfusionMatrix


class DomainShiftAnalysis(BaseModel):
    f1_retention_percentage: float
    precision_delta: float
    recall_delta: float
    generalization_verdict: str  # 'EXCELLENT', 'ROBUST', 'MODERATE_DEGRADATION', 'SIGNIFICANT_SHIFT'
    key_observations: List[str]


class ValidationComparisonResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    success: bool
    evaluated_at: str
    model_name: str
    decision_threshold: float
    internal_benchmark: DatasetMetricSummary
    external_benchmark: DatasetMetricSummary
    domain_shift: DomainShiftAnalysis
    recommendations: List[str]

