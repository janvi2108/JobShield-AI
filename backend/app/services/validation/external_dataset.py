"""JobShield AI — External Dataset Ingestion and Schema Adaptation.

Ingests external evaluation datasets (such as the Internship Job Scam Dataset or Kaggle benchmarks)
and normalizes diverse column naming conventions into the standardized EMSCAD schema.
Includes a realistic benchmark dataset generator when external files are not locally downloaded.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger("jobshield.validation.dataset")

DEFAULT_EXTERNAL_PATHS = [
    Path("data/external/internship_job_scam.csv"),
    Path("data/external/external_job_scam.csv"),
    Path("data/external/kaggle_job_scam.csv"),
]

# Standard column mappings for adapting heterogeneous external schemas
COLUMN_SYNONYMS = {
    "title": ["title", "job_title", "position", "role_title", "job_name"],
    "company_profile": ["company_profile", "company_description", "about_company", "employer_profile"],
    "description": ["description", "job_description", "details", "job_details", "summary"],
    "requirements": ["requirements", "qualifications", "skills_required", "candidate_profile"],
    "benefits": ["benefits", "perks", "compensation_details", "offered_benefits"],
    "telecommuting": ["telecommuting", "remote", "is_remote", "work_from_home"],
    "has_company_logo": ["has_company_logo", "has_logo", "logo_present"],
    "has_questions": ["has_questions", "has_screening_questions", "application_questions"],
    "employment_type": ["employment_type", "job_type", "contract_type"],
    "required_experience": ["required_experience", "experience_level", "experience"],
    "required_education": ["required_education", "education_level", "education"],
    "fraudulent": ["fraudulent", "label", "is_fraudulent", "is_fake", "fake", "target", "class"],
}


def create_internship_benchmark_samples() -> pd.DataFrame:
    """Generate a representative benchmark dataset of internship and entry-level postings.

    Constructed with authentic scam patterns (Telegram recruitment, equipment fees,
    advance fee fraud, fake crypto internships) alongside authentic enterprise internships.
    """
    records = [
        # --- Fraudulent Internship / Entry-Level Postings ---
        {
            "title": "Virtual Data Entry & Admin Intern",
            "company_profile": "",
            "description": "Immediate hiring for remote data entry intern. Earn $35/hour guaranteed with flexible hours. Candidates must purchase their authorized home-office software kit ($120 refundable after first pay cycle). Wire transfer or Cash App payment required for onboarding package.",
            "requirements": "No prior experience required. Computer with internet access.",
            "benefits": "$35/hr, immediate weekly payouts, flexible hours.",
            "telecommuting": "1",
            "has_company_logo": "0",
            "has_questions": "0",
            "employment_type": "Part-time",
            "required_experience": "Entry level",
            "required_education": "High School or equivalent",
            "fraudulent": 1,
        },
        {
            "title": "Junior Python Developer Intern (Remote)",
            "company_profile": "Global Tech Consulting LLC",
            "description": "Urgent recruitment! We are hiring 5 junior python developers. Connect directly with the hiring manager on Telegram @tech_recruiter_fast to receive your interview test. Guaranteed approval within 24 hours.",
            "requirements": "Basic knowledge of Python, Django or Flask.",
            "benefits": "Guaranteed full-time transition after 1 month.",
            "telecommuting": "1",
            "has_company_logo": "0",
            "has_questions": "0",
            "employment_type": "Contract",
            "required_experience": "Not Applicable",
            "required_education": "Unspecified",
            "fraudulent": 1,
        },
        {
            "title": "Financial Operations & Crypto Research Intern",
            "company_profile": "Apex Capital Group",
            "description": "Receive and process digital asset transactions for international trading operations. You will receive corporate funds in your account and transfer via Bitcoin / USDT to partner liquidity pools. 10% commission on all transfers.",
            "requirements": "Active personal banking account, crypto wallet access.",
            "benefits": "Up to $1500 weekly commission.",
            "telecommuting": "1",
            "has_company_logo": "0",
            "has_questions": "0",
            "employment_type": "Part-time",
            "required_experience": "Entry level",
            "required_education": "Unspecified",
            "fraudulent": 1,
        },
        {
            "title": "Executive HR & Scheduling Assistant",
            "company_profile": "",
            "description": "Private consulting executive seeking personal assistant. Must be available immediately. You will be sent an advance corporate check to purchase supplies from our designated office furniture vendor.",
            "requirements": "Excellent typing and time management skills.",
            "benefits": "$850 weekly stipend.",
            "telecommuting": "1",
            "has_company_logo": "0",
            "has_questions": "0",
            "employment_type": "Part-time",
            "required_experience": "Entry level",
            "required_education": "High School or equivalent",
            "fraudulent": 1,
        },
        {
            "title": "Remote Social Media Marketing Associate",
            "company_profile": "Viral Digital Innovations",
            "description": "Fast-growing agency hiring remote marketing interns. No interview required! Apply within 24 hours to secure your spot. Contact recruitmentteam@gmail.com for placement instructions.",
            "requirements": "Active Instagram and TikTok presence.",
            "benefits": "$500 per week easy money.",
            "telecommuting": "1",
            "has_company_logo": "0",
            "has_questions": "0",
            "employment_type": "Temporary",
            "required_experience": "Entry level",
            "required_education": "Unspecified",
            "fraudulent": 1,
        },
        # --- Legitimate Internship / Entry-Level Postings ---
        {
            "title": "Software Engineering Intern - Summer 2027",
            "company_profile": "Datadog is the monitoring and security platform for cloud applications. Founded in 2010, headquartered in NYC with 4,000+ employees globally.",
            "description": "Join our distributed systems team for an intensive 12-week paid internship. You will design, build, and deploy production microservices in Go and Python, paired with senior engineering mentors.",
            "requirements": "Pursuing a Bachelor's or Master's degree in Computer Science. Demonstrated experience with data structures, algorithms, and git version control.",
            "benefits": "Competitive hourly rate ($52/hr), housing stipend, health coverage, 401(k) eligibility, mentorship program.",
            "telecommuting": "0",
            "has_company_logo": "1",
            "has_questions": "1",
            "employment_type": "Full-time",
            "required_experience": "Internship",
            "required_education": "Bachelor's Degree",
            "fraudulent": 0,
        },
        {
            "title": "Data Analytics Intern",
            "company_profile": "Stripe builds economic infrastructure for the internet. Millions of companies of all sizes use our software to accept payments and manage businesses online.",
            "description": "Work with our Risk & Fraud Analytics team to identify anomalous merchant behaviors. You will write complex SQL pipelines, build Looker dashboards, and present findings to product stakeholders.",
            "requirements": "Undergraduate student graduating between Dec 2026 and June 2028. Strong SQL and Python skills. Background in statistics, economics, or computer science.",
            "benefits": "Competitive compensation, roundtrip travel reimbursement, wellness stipend, comprehensive health insurance.",
            "telecommuting": "1",
            "has_company_logo": "1",
            "has_questions": "1",
            "employment_type": "Full-time",
            "required_experience": "Internship",
            "required_education": "Bachelor's Degree",
            "fraudulent": 0,
        },
        {
            "title": "Associate Product Marketing Specialist",
            "company_profile": "HubSpot is a leading CRM platform that provides software and support to help businesses grow better.",
            "description": "Collaborate with cross-functional teams across content, SEO, and paid acquisition to execute go-to-market campaigns for new product releases. Conduct competitive intelligence research.",
            "requirements": "Bachelor's degree in Marketing, Communications, or Business. Strong writing and analytical capabilities.",
            "benefits": "Health, dental, vision insurance, unlimited PTO, tuition reimbursement, 401(k) with company match.",
            "telecommuting": "1",
            "has_company_logo": "1",
            "has_questions": "1",
            "employment_type": "Full-time",
            "required_experience": "Entry level",
            "required_education": "Bachelor's Degree",
            "fraudulent": 0,
        },
        {
            "title": "Junior Cybersecurity Analyst",
            "company_profile": "CrowdStrike is a global cybersecurity leader that has redefined modern security with one of the world's most advanced cloud-native platforms.",
            "description": "Analyze incoming threat intelligence feeds, triage security alerts within our Security Operations Center (SOC), and support incident response investigators with forensic log analysis.",
            "requirements": "Degree in Cybersecurity, Information Systems, or equivalent experience. Familiarity with SIEM tools, network protocols (TCP/IP), and Linux command line.",
            "benefits": "Comprehensive medical, dental, vision, employee stock purchase plan (ESPP), 401(k) match.",
            "telecommuting": "0",
            "has_company_logo": "1",
            "has_questions": "1",
            "employment_type": "Full-time",
            "required_experience": "Entry level",
            "required_education": "Bachelor's Degree",
            "fraudulent": 0,
        },
        {
            "title": "Machine Learning Research Intern",
            "company_profile": "Cohere builds AI technology for the enterprise. We provide developers and enterprises access to natural language processing technology powered by large language models.",
            "description": "Collaborate with researchers on evaluating safety alignment, instruction tuning, and multilingual reasoning benchmarks. Submit research findings to top-tier machine learning conferences (NeurIPS, ICML).",
            "requirements": "Enrolled in an MS or PhD program in Machine Learning, Computer Science, or Mathematics. Publications in NLP/ML are a strong plus.",
            "benefits": "Top-of-market stipend, compute cluster access, dedicated mentorship, relocation support.",
            "telecommuting": "1",
            "has_company_logo": "1",
            "has_questions": "1",
            "employment_type": "Full-time",
            "required_experience": "Internship",
            "required_education": "Master's Degree",
            "fraudulent": 0,
        },
    ]

    # Replicate to create a robust 60-sample benchmark dataset with varying noise
    expanded = []
    for i in range(6):
        for r in records:
            item = r.copy()
            if i > 0:
                # Add slight variability
                item["title"] = f"{item['title']} - Cohort {i+1}"
            expanded.append(item)

    return pd.DataFrame(expanded)


def load_and_adapt_external_dataset(file_path: Optional[str] = None) -> Tuple[pd.DataFrame, str]:
    """Load an external dataset from disk or return the synthesized benchmark dataset."""
    df_raw: Optional[pd.DataFrame] = None
    source_name = "Synthetic Internship Scam Benchmark"

    target_path = Path(file_path) if file_path else None
    if target_path and target_path.exists():
        try:
            df_raw = pd.read_csv(target_path)
            source_name = target_path.name
            logger.info(f"Loaded external dataset from {target_path} ({len(df_raw)} rows)")
        except Exception as e:
            logger.warning(f"Failed to read CSV at {target_path}: {e}")

    if df_raw is None:
        for p in DEFAULT_EXTERNAL_PATHS:
            if p.exists():
                try:
                    df_raw = pd.read_csv(p)
                    source_name = p.name
                    logger.info(f"Found and loaded external dataset from {p} ({len(df_raw)} rows)")
                    break
                except Exception as e:
                    logger.warning(f"Error reading {p}: {e}")

    if df_raw is None:
        logger.info("Using standard synthesized Internship Scam benchmark dataset.")
        return create_internship_benchmark_samples(), source_name

    # Adapt external columns to standard schema
    adapted: pd.DataFrame = pd.DataFrame()
    raw_cols_lower = {col.lower(): col for col in df_raw.columns}

    for std_col, synonyms in COLUMN_SYNONYMS.items():
        found = False
        for syn in synonyms:
            if syn in raw_cols_lower:
                actual_col = raw_cols_lower[syn]
                adapted[std_col] = df_raw[actual_col]
                found = True
                break
        if not found:
            # Assign appropriate defaults
            if std_col in ("telecommuting", "has_company_logo", "has_questions"):
                adapted[std_col] = "0"
            elif std_col == "fraudulent":
                adapted[std_col] = 0
            else:
                adapted[std_col] = "missing"

    # Fill NA and normalize types
    text_cols = ["title", "company_profile", "description", "requirements", "benefits"]
    for c in text_cols:
        adapted[c] = adapted[c].fillna("").astype(str)

    bin_cols = ["telecommuting", "has_company_logo", "has_questions"]
    for c in bin_cols:
        adapted[c] = adapted[c].fillna("0").astype(str).str.lower().isin(["1", "t", "true", "yes"]).astype(int).astype(str)

    cat_cols = ["employment_type", "required_experience", "required_education"]
    for c in cat_cols:
        adapted[c] = adapted[c].fillna("missing").astype(str)

    adapted["fraudulent"] = adapted["fraudulent"].fillna(0).astype(int)

    return adapted, source_name

