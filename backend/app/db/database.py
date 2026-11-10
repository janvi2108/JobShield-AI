"""JobShield AI — SQLAlchemy Database Layer.

Provides local SQLite and PostgreSQL-compatible persistence for job analyses,
ML predictions, extracted attributes, heuristic evidence findings, and explanations.

Uses SQLAlchemy 2.0 ORM with safe transaction management and cascades.
Database operations are fully independent of any external AI API key.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from sqlalchemy import create_engine, func, select, or_, desc, delete
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db.models import (
    Base,
    JobAnalysis,
    FraudPrediction,
    ExtractedDetails,
    EvidenceFinding,
    AIExplanation,
    _utcnow,
)

logger = logging.getLogger("jobshield.database")

# Default database path — project root / jobshield.db
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "jobshield.db"


def _get_database_url(db_path: Optional[Path] = None) -> str:
    """Resolve database URL for SQLAlchemy engine."""
    if db_path is not None:
        return f"sqlite:///{db_path.resolve().as_posix()}"
    env_url = os.environ.get("DATABASE_URL", "")
    if env_url:
        return env_url
    return f"sqlite:///{_DEFAULT_DB_PATH.resolve().as_posix()}"


def _get_engine(db_path: Optional[Path] = None):
    url = _get_database_url(db_path)
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(url, connect_args=connect_args, echo=False)


# Default engine and sessionmaker
_engine = _get_engine()
_SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False, autoflush=False)


def get_connection(db_path: Optional[Path] = None):
    """Legacy helper for direct sqlite connection check (e.g., in health check)."""
    import sqlite3
    path = db_path or _DEFAULT_DB_PATH
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _get_db_path() -> Path:
    env_url = os.environ.get("DATABASE_URL", "")
    if env_url.startswith("sqlite:///"):
        rel = env_url[len("sqlite:///"):]
        return Path(rel).resolve()
    return _DEFAULT_DB_PATH


@contextmanager
def get_session(db_path: Optional[Path] = None) -> Generator[Session, None, None]:
    """Provide a transactional SQLAlchemy database session."""
    engine = _engine if db_path is None else _get_engine(db_path)
    factory = _SessionFactory if db_path is None else sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(db_path: Optional[Path] = None) -> None:
    """Create all tables defined in Base metadata."""
    engine = _engine if db_path is None else _get_engine(db_path)
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database schema initialized successfully via SQLAlchemy.")


# ---------------------------------------------------------------------------
# Core Analysis Persistence (Atomic Multi-Table Insert)
# ---------------------------------------------------------------------------

def save_analysis(
    title: str,
    company: str,
    description: str,
    is_fraudulent: bool,
    fraud_probability: float,
    risk_level: str,
    verdict: str,
    decision_threshold: float,
    model_name: str,
    model_status: str,
    heuristic_signals: Optional[List[str]] = None,
    shap_values: Optional[List[Dict[str, Any]]] = None,
    grounded_explanation: Optional[Dict[str, Any]] = None,
    requirements: str = "",
    benefits: str = "",
    employment_type: str = "",
    required_experience: str = "",
    required_education: str = "",
    telecommuting: bool = False,
    has_company_logo: bool = False,
    has_questions: bool = False,
    source_type: str = "manual",
    raw_input_snippet: str = "",
    extracted_job: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Persist a complete job analysis atomically across all 5 relational models.
    
    Returns the integer primary key of the new JobAnalysis record.
    """
    signals = heuristic_signals or []
    shaps = []
    if shap_values:
        for s in shap_values:
            if hasattr(s, "model_dump"):
                shaps.append(s.model_dump())
            elif isinstance(s, dict):
                shaps.append(s)
            else:
                shaps.append({"token": getattr(s, "token", str(s)), "value": getattr(s, "value", 0.0)})

    with get_session(db_path) as session:
        # 1. Parent JobAnalysis
        analysis = JobAnalysis(
            title=title or "Untitled Position",
            company=company or "Confidential / Unspecified",
            description=description,
            source_url=extracted_job.get("source_url") if extracted_job else None,
            input_type=source_type,
            status="completed",
        )
        session.add(analysis)
        session.flush()  # populate analysis.id

        # 2. FraudPrediction
        prediction = FraudPrediction(
            analysis_id=analysis.id,
            is_fraudulent=bool(is_fraudulent),
            fraud_probability=float(fraud_probability),
            risk_level=risk_level or "LOW",
            verdict=verdict or "Evaluated",
            decision_threshold=float(decision_threshold),
            model_name=model_name or "Linear Support Vector Machine",
            model_version=model_status or "trained",
            heuristic_signals=json.dumps(signals),
            shap_values=json.dumps(shaps),
            predicted_at=_utcnow(),
        )
        session.add(prediction)

        # 3. ExtractedDetails
        ext_dict = extracted_job or {}
        extracted = ExtractedDetails(
            analysis_id=analysis.id,
            job_title=ext_dict.get("title") or title,
            company_name=ext_dict.get("company_name") or company,
            location=ext_dict.get("location"),
            employment_type=ext_dict.get("employment_type") or employment_type,
            required_experience=ext_dict.get("required_experience") or required_experience,
            required_education=ext_dict.get("required_education") or required_education,
            compensation=ext_dict.get("compensation") or ext_dict.get("salary_range"),
            duration=ext_dict.get("duration"),
            work_arrangement=ext_dict.get("work_arrangement"),
            required_skills=json.dumps(ext_dict.get("required_skills") or []),
            requirements=ext_dict.get("requirements") or requirements,
            responsibilities=ext_dict.get("responsibilities"),
            extraction_confidence=ext_dict.get("extraction_confidence"),
            completeness_score=ext_dict.get("completeness_score"),
            missing_fields=json.dumps(ext_dict.get("missing_fields") or []),
            extraction_method=ext_dict.get("extraction_method") or source_type,
        )
        session.add(extracted)

        # 4. EvidenceFindings (one row per detected heuristic threat signal)
        for sig in signals:
            sig_text = str(sig)
            cat = "general"
            sig_lower = sig_text.lower()
            if "fee" in sig_lower or "money" in sig_lower or "transfer" in sig_lower or "crypto" in sig_lower:
                cat = "financial"
            elif "telegram" in sig_lower or "whatsapp" in sig_lower or "chat" in sig_lower or "webmail" in sig_lower:
                cat = "communication"
            elif "urgent" in sig_lower or "pressure" in sig_lower or "fast" in sig_lower:
                cat = "urgency"
            elif "guarantee" in sig_lower or "no experience" in sig_lower:
                cat = "claim"
            elif "logo" in sig_lower:
                cat = "verification"

            severity = "critical" if ("fee" in sig_lower or "wire" in sig_lower or "transfer" in sig_lower) else "high"

            finding = EvidenceFinding(
                analysis_id=analysis.id,
                category=cat,
                indicator_name=sig_text[:300],
                description=sig_text,
                severity=severity,
                evidence_text=sig_text,
                source_type="heuristic_scan",
                detected_at=_utcnow(),
            )
            session.add(finding)

        # 5. AIExplanation
        if grounded_explanation:
            g = grounded_explanation
            summary = g.get("overall_summary") or "Analysis completed."
            reasons = g.get("primary_reasons") or []
            checklist = g.get("verification_checklist") or []
            verdict_text = g.get("applicant_safety_verdict") or verdict
            method = g.get("generation_method") or "deterministic_grounded_fallback"

            explanation = AIExplanation(
                analysis_id=analysis.id,
                overall_summary=summary,
                primary_reasons=json.dumps(reasons),
                verification_checklist=json.dumps(checklist),
                applicant_safety_verdict=verdict_text,
                generation_method=method,
                provider_name="groq" if "groq" in method else "local",
                model_identifier="local_deterministic" if "deterministic" in method else "llama-3.3-70b-versatile",
                generated_at=_utcnow(),
            )
            session.add(explanation)

        session.flush()
        return analysis.id


# ---------------------------------------------------------------------------
# Retrieval & Querying Functions
# ---------------------------------------------------------------------------

def get_recent_analyses(limit: int = 20, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Retrieve recent analyses formatted for backward-compatible history endpoint."""
    with get_session(db_path) as session:
        stmt = select(JobAnalysis).order_by(desc(JobAnalysis.created_at)).limit(limit)
        results = session.scalars(stmt).all()
        output = []
        for a in results:
            item: Dict[str, Any] = {
                "id": a.id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "title": a.title,
                "company": a.company,
                "description": a.description,
                "source_type": a.input_type,
            }
            if a.prediction:
                item["is_fraudulent"] = int(a.prediction.is_fraudulent)
                item["fraud_probability"] = a.prediction.fraud_probability
                item["risk_level"] = a.prediction.risk_level
                item["verdict"] = a.prediction.verdict
                item["decision_threshold"] = a.prediction.decision_threshold
                item["model_name"] = a.prediction.model_name
                item["model_status"] = a.prediction.model_version
                try:
                    item["heuristic_signals"] = json.loads(a.prediction.heuristic_signals or "[]")
                except Exception:
                    item["heuristic_signals"] = []
                try:
                    item["shap_values"] = json.loads(a.prediction.shap_values or "[]")
                except Exception:
                    item["shap_values"] = []
            else:
                item["is_fraudulent"] = 0
                item["fraud_probability"] = 0.0
                item["risk_level"] = "UNKNOWN"
                item["heuristic_signals"] = []
                item["shap_values"] = []

            if a.explanation:
                try:
                    reasons = json.loads(a.explanation.primary_reasons or "[]")
                except Exception:
                    reasons = []
                try:
                    checklist = json.loads(a.explanation.verification_checklist or "[]")
                except Exception:
                    checklist = []
                item["grounded_explanation"] = {
                    "overall_summary": a.explanation.overall_summary,
                    "primary_reasons": reasons,
                    "verification_checklist": checklist,
                    "applicant_safety_verdict": a.explanation.applicant_safety_verdict,
                    "generation_method": a.explanation.generation_method,
                }
            else:
                item["grounded_explanation"] = None

            output.append(item)
        return output


def get_analysis_by_id(analysis_id: int, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Retrieve full analysis tree by primary key."""
    with get_session(db_path) as session:
        analysis = session.get(JobAnalysis, analysis_id)
        if not analysis:
            return None

        # Build full composite response
        pred = analysis.prediction
        ext = analysis.extracted_details
        exp = analysis.explanation
        findings = analysis.evidence_findings or []

        try:
            heuristics = json.loads(pred.heuristic_signals or "[]") if pred else []
        except Exception:
            heuristics = []
        try:
            shaps = json.loads(pred.shap_values or "[]") if pred else []
        except Exception:
            shaps = []
        try:
            skills = json.loads(ext.required_skills or "[]") if ext else []
        except Exception:
            skills = []
        try:
            missing = json.loads(ext.missing_fields or "[]") if ext else []
        except Exception:
            missing = []

        grounded_data = None
        if exp:
            try:
                reasons = json.loads(exp.primary_reasons or "[]")
            except Exception:
                reasons = []
            try:
                checklist = json.loads(exp.verification_checklist or "[]")
            except Exception:
                checklist = []
            grounded_data = {
                "overall_summary": exp.overall_summary,
                "primary_reasons": reasons,
                "verification_checklist": checklist,
                "applicant_safety_verdict": exp.applicant_safety_verdict,
                "generation_method": exp.generation_method,
                "provider_name": exp.provider_name,
                "model_identifier": exp.model_identifier,
                "generated_at": exp.generated_at.isoformat() if exp.generated_at else None,
            }

        findings_list = [
            {
                "id": f.id,
                "category": f.category,
                "indicator_name": f.indicator_name,
                "description": f.description,
                "severity": f.severity,
                "evidence_text": f.evidence_text,
                "detected_at": f.detected_at.isoformat() if f.detected_at else None,
            }
            for f in findings
        ]

        return {
            "id": analysis.id,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None,
            "title": analysis.title,
            "company": analysis.company,
            "description": analysis.description,
            "source_url": analysis.source_url,
            "input_type": analysis.input_type,
            "status": analysis.status,
            "is_fraudulent": int(pred.is_fraudulent) if pred else 0,
            "fraud_probability": pred.fraud_probability if pred else 0.0,
            "risk_level": pred.risk_level if pred else "UNKNOWN",
            "verdict": pred.verdict if pred else "",
            "decision_threshold": pred.decision_threshold if pred else 0.5,
            "model_name": pred.model_name if pred else "",
            "model_status": pred.model_version if pred else "trained",
            "heuristic_signals": heuristics,
            "shap_values": shaps,
            "extracted_details": {
                "job_title": ext.job_title if ext else analysis.title,
                "company_name": ext.company_name if ext else analysis.company,
                "location": ext.location if ext else None,
                "employment_type": ext.employment_type if ext else None,
                "required_experience": ext.required_experience if ext else None,
                "required_education": ext.required_education if ext else None,
                "compensation": ext.compensation if ext else None,
                "duration": ext.duration if ext else None,
                "work_arrangement": ext.work_arrangement if ext else None,
                "required_skills": skills,
                "requirements": ext.requirements if ext else None,
                "responsibilities": ext.responsibilities if ext else None,
                "extraction_confidence": ext.extraction_confidence if ext else None,
                "completeness_score": ext.completeness_score if ext else None,
                "missing_fields": missing,
                "extraction_method": ext.extraction_method if ext else "manual",
            } if ext else None,
            "evidence_findings": findings_list,
            "grounded_explanation": grounded_data,
        }


def get_analyses_list(
    page: int = 1,
    page_size: int = 20,
    search_title: Optional[str] = None,
    search_company: Optional[str] = None,
    classification: Optional[str] = None,
    risk_level: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> Tuple[List[Dict[str, Any]], int, int]:
    """Return paginated analyses with search and filtering, along with total records and pages."""
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    with get_session(db_path) as session:
        query = select(JobAnalysis).outerjoin(JobAnalysis.prediction)

        if search_title:
            query = query.where(JobAnalysis.title.ilike(f"%{search_title}%"))
        if search_company:
            query = query.where(JobAnalysis.company.ilike(f"%{search_company}%"))
        if classification:
            c = classification.lower()
            if c in ("fraudulent", "fraud", "1", "true"):
                query = query.where(FraudPrediction.is_fraudulent.is_(True))
            elif c in ("legitimate", "legit", "0", "false"):
                query = query.where(FraudPrediction.is_fraudulent.is_(False))
        if risk_level:
            query = query.where(FraudPrediction.risk_level == risk_level.upper())

        # Total count query
        count_stmt = select(func.count()).select_from(query.subquery())
        total_count = session.scalar(count_stmt) or 0
        total_pages = max(1, (total_count + page_size - 1) // page_size) if total_count > 0 else 1

        # Fetch page items
        stmt = query.order_by(desc(JobAnalysis.created_at)).offset((page - 1) * page_size).limit(page_size)
        records = session.scalars(stmt).all()

        items = []
        for a in records:
            pred = a.prediction
            items.append({
                "id": a.id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "title": a.title,
                "company": a.company,
                "is_fraudulent": bool(pred.is_fraudulent) if pred else False,
                "fraud_probability": pred.fraud_probability if pred else 0.0,
                "risk_level": pred.risk_level if pred else "LOW",
                "verdict": pred.verdict if pred else "",
                "input_type": a.input_type,
            })

        return items, total_count, total_pages


def delete_analysis(analysis_id: int, db_path: Optional[Path] = None) -> bool:
    """Delete an analysis and all its cascading dependents (prediction, evidence, etc.)."""
    with get_session(db_path) as session:
        analysis = session.get(JobAnalysis, analysis_id)
        if not analysis:
            return False
        session.delete(analysis)
        session.flush()
        return True


def get_analysis_stats(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Compute live, non-fabricated database metrics from actual saved analyses."""
    with get_session(db_path) as session:
        # Total analyses
        total_stmt = select(func.count(JobAnalysis.id))
        total_count = session.scalar(total_stmt) or 0

        # Fraudulent vs legitimate
        fraud_stmt = (
            select(func.count(FraudPrediction.id))
            .where(FraudPrediction.is_fraudulent.is_(True))
        )
        fraud_count = session.scalar(fraud_stmt) or 0

        legit_stmt = (
            select(func.count(FraudPrediction.id))
            .where(FraudPrediction.is_fraudulent.is_(False))
        )
        legit_count = session.scalar(legit_stmt) or 0

        # High-risk (CRITICAL + HIGH)
        high_risk_stmt = (
            select(func.count(FraudPrediction.id))
            .where(FraudPrediction.risk_level.in_(["CRITICAL", "HIGH"]))
        )
        high_risk_count = session.scalar(high_risk_stmt) or 0

        # Analyses today (UTC)
        today_start = datetime.datetime.now(datetime.timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_stmt = (
            select(func.count(JobAnalysis.id))
            .where(JobAnalysis.created_at >= today_start)
        )
        today_count = session.scalar(today_stmt) or 0

        fraud_pct = round((fraud_count / total_count * 100.0), 2) if total_count > 0 else 0.0

        return {
            "total_analyses": total_count,
            "fraudulent_count": fraud_count,
            "legitimate_count": legit_count,
            "high_risk_count": high_risk_count,
            "today_count": today_count,
            "fraud_percentage": fraud_pct,
        }


# ---------------------------------------------------------------------------
# Extraction Results Persistence
# ---------------------------------------------------------------------------

def save_extraction(
    source_type: str,
    source_ref: str,
    extracted_data: Dict[str, Any],
    completeness_score: float = 0.0,
    extraction_confidence: float = 0.0,
    extraction_method: str = "",
    is_valid_job: bool = True,
    warnings: Optional[List[str]] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Save raw extraction result record."""
    from backend.app.db.models import ExtractionResult
    with get_session(db_path) as session:
        ext = ExtractionResult(
            source_type=source_type,
            source_ref=source_ref[:2048] if source_ref else None,
            is_valid_job=bool(is_valid_job),
            extracted_data=json.dumps(extracted_data or {}),
            completeness_score=float(completeness_score) if completeness_score is not None else None,
            extraction_confidence=float(extraction_confidence) if extraction_confidence is not None else None,
            extraction_method=extraction_method,
            warnings=json.dumps(warnings or []),
            created_at=_utcnow(),
        )
        session.add(ext)
        session.flush()
        return ext.id


def get_recent_extractions(limit: int = 20, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Retrieve recent extraction attempts."""
    from backend.app.db.models import ExtractionResult
    with get_session(db_path) as session:
        stmt = select(ExtractionResult).order_by(desc(ExtractionResult.created_at)).limit(limit)
        results = session.scalars(stmt).all()
        output = []
        for r in results:
            try:
                data_dict = json.loads(r.extracted_data or "{}")
            except Exception:
                data_dict = {}
            try:
                warn_list = json.loads(r.warnings or "[]")
            except Exception:
                warn_list = []
            output.append({
                "id": r.id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "source_type": r.source_type,
                "source_ref": r.source_ref,
                "is_valid_job": bool(r.is_valid_job),
                "extracted_data": data_dict,
                "completeness_score": r.completeness_score,
                "extraction_confidence": r.extraction_confidence,
                "extraction_method": r.extraction_method,
                "warnings": warn_list,
            })
        return output

