"""JobShield AI — Extracted Field Normalizer.

Calculates completeness scores, identifies missing information, and normalizes
extracted structured fields into standard JobAnalysisRequest payloads compatible
with the champion Linear SVM classification pipeline.
"""

from __future__ import annotations

from typing import List, Tuple
from backend.app.schemas.analysis import JobAnalysisRequest
from backend.app.schemas.extraction import ExtractedJobData


CORE_ATTRIBUTES = [
    "title",
    "company_name",
    "location",
    "employment_type",
    "salary_range",
    "required_experience",
    "required_education",
    "requirements",
    "responsibilities",
]


def evaluate_completeness(data: ExtractedJobData) -> Tuple[float, List[str]]:
    """Calculate ratio of populated core fields and return list of missing attributes."""
    missing = []
    populated_count = 0

    for attr in CORE_ATTRIBUTES:
        val = getattr(data, attr, None)
        if attr == "salary_range" and not val:
            val = getattr(data, "compensation", None)
        if val is None or (isinstance(val, (str, list)) and len(val) == 0) or str(val).lower() == "not specified":
            missing.append(attr)
        else:
            populated_count += 1

    score = round(populated_count / len(CORE_ATTRIBUTES), 2)
    return score, missing


def normalize_to_analysis_request(data: ExtractedJobData, raw_text: str = "") -> JobAnalysisRequest:
    """Convert extracted job fields into a validated JobAnalysisRequest for the ML model."""
    title = data.title or "Job Posting Under Analysis"
    company_name = data.company_name or ""
    company_profile = data.company_profile or data.company_description or ""

    # Assemble description
    desc_parts = []
    if data.description:
        desc_parts.append(str(data.description))
    if data.responsibilities and data.responsibilities not in str(data.description or ""):
        desc_parts.append("Responsibilities:\n" + str(data.responsibilities))
    if data.requirements and data.requirements not in str(data.description or ""):
        desc_parts.append("Requirements:\n" + str(data.requirements))
    if data.application_instructions:
        desc_parts.append("Application Instructions:\n" + str(data.application_instructions))
    if data.fee_details:
        desc_parts.append("Fee & Payment Information:\n" + str(data.fee_details))

    assembled_desc = "\n\n".join(desc_parts)
    final_desc = assembled_desc if len(assembled_desc.strip()) >= 50 else (raw_text or assembled_desc or "No detailed description provided.")

    # Requirements
    req_text = data.requirements or ""
    if data.required_skills:
        req_text += "\nSkills: " + ", ".join(data.required_skills)

    # Benefits
    benefits_text = data.benefits or ""
    if data.salary_range:
        benefits_text += "\nCompensation: " + str(data.salary_range)

    # Telecommuting flag
    telecommuting = bool(data.is_remote or data.telecommuting) if (data.is_remote is not None or data.telecommuting is not None) else False

    # Company logo flag heuristic: genuine corporate postings usually have corporate domain / profile
    has_logo = bool(data.has_company_logo if data.has_company_logo is not None else (data.company_name and len(data.company_name) > 2))

    return JobAnalysisRequest(
        title=title[:300],
        company_name=company_name[:200],
        company_profile=company_profile[:5000],
        description=final_desc[:50000],
        requirements=req_text[:15000],
        benefits=benefits_text[:10000],
        telecommuting=telecommuting,
        has_company_logo=has_logo,
        has_questions=bool(data.has_questions if data.has_questions is not None else data.application_instructions),
        employment_type=data.employment_type or "",
        required_experience=data.required_experience or "",
        required_education=data.required_education or "",
    )
