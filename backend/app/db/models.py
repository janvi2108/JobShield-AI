"""JobShield AI — SQLAlchemy ORM Models.

Defines the declarative model classes for the JobShield AI database schema.
Supports SQLite (default) and PostgreSQL via DATABASE_URL environment variable.
No external API key required.
"""

from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime.datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.datetime.now(datetime.timezone.utc)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ---------------------------------------------------------------------------
# Table 1: job_analyses
# ---------------------------------------------------------------------------

class JobAnalysis(Base):
    """Top-level record representing a single job posting analysis session."""

    __tablename__ = "job_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    input_type: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)

    # Relationships (cascade delete-orphan so removing a JobAnalysis removes all children)
    prediction: Mapped[Optional["FraudPrediction"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        uselist=False,
    )
    extracted_details: Mapped[Optional["ExtractedDetails"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        uselist=False,
    )
    evidence_findings: Mapped[List["EvidenceFinding"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    explanation: Mapped[Optional["AIExplanation"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (
        Index("idx_analyses_created_at", "created_at"),
        Index("idx_analyses_company", "company"),
        Index("idx_analyses_title", "title"),
    )


# ---------------------------------------------------------------------------
# Table 2: fraud_predictions
# ---------------------------------------------------------------------------

class FraudPrediction(Base):
    """ML model prediction output for a single analysis."""

    __tablename__ = "fraud_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_analyses.id", ondelete="CASCADE"), nullable=False
    )
    is_fraudulent: Mapped[bool] = mapped_column(nullable=False, default=False)
    fraud_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW")
    verdict: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    decision_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    heuristic_signals: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON
    shap_values: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON
    predicted_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    analysis: Mapped["JobAnalysis"] = relationship(back_populates="prediction")

    __table_args__ = (
        Index("idx_analyses_is_fraudulent", "is_fraudulent"),
        Index("idx_analyses_risk_level", "risk_level"),
    )


# ---------------------------------------------------------------------------
# Table 3: extracted_details
# ---------------------------------------------------------------------------

class ExtractedDetails(Base):
    """Structured job-detail fields parsed from the raw posting text."""

    __tablename__ = "extracted_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_analyses.id", ondelete="CASCADE"), nullable=False
    )
    job_title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    required_experience: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    required_education: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    compensation: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    work_arrangement: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    required_skills: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON list
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    completeness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    missing_fields: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON list
    extraction_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    analysis: Mapped["JobAnalysis"] = relationship(back_populates="extracted_details")


# ---------------------------------------------------------------------------
# Table 4: evidence_findings
# ---------------------------------------------------------------------------

class EvidenceFinding(Base):
    """Individual heuristic signal / evidence item detected in the posting."""

    __tablename__ = "evidence_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_analyses.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    indicator_name: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    evidence_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    detected_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    analysis: Mapped["JobAnalysis"] = relationship(back_populates="evidence_findings")


# ---------------------------------------------------------------------------
# Table 5: ai_explanations
# ---------------------------------------------------------------------------

class AIExplanation(Base):
    """LLM or deterministic AI-generated explanation for the fraud verdict."""

    __tablename__ = "ai_explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_analyses.id", ondelete="CASCADE"), nullable=False
    )
    overall_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    primary_reasons: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON
    verification_checklist: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON
    applicant_safety_verdict: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_method: Mapped[str] = mapped_column(String(100), nullable=False, default="deterministic_grounded_fallback")
    provider_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_identifier: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    generated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    analysis: Mapped["JobAnalysis"] = relationship(back_populates="explanation")


# ---------------------------------------------------------------------------
# Table 6: extraction_results (Retained for backwards compatibility)
# ---------------------------------------------------------------------------

class ExtractionResult(Base):
    """Record of individual extraction attempts from raw input."""

    __tablename__ = "extraction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_ref: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    is_valid_job: Mapped[bool] = mapped_column(nullable=False, default=True)
    extracted_data: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    completeness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extraction_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    warnings: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

