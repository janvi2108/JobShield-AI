"""JobShield AI — Content Validator & Job Detection Service.

Validates that submitted text or fetched URL content represents a genuine,
usable job/internship posting rather than technical website configurations,
JavaScript theme blobs, privacy cookies, or unrelated code metadata.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("jobshield.extraction.validator")


class ContentValidationResult(BaseModel):
    is_valid_job: bool = Field(..., description="True if content resembles a genuine job posting")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in content validity")
    error_message: Optional[str] = Field(default=None, description="User-facing error if invalid")
    detected_issues: List[str] = Field(default_factory=list, description="Specific non-job indicators detected")
    job_signal_score: float = Field(default=0.0, description="Relative density of recruitment terminology")


# Known configuration keys and metadata indicators that identify web configs, not jobs
TECHNICAL_CONFIG_KEYS = [
    "themeoptions", "customtheme", "vartheme", "primary-color", "secondary-color",
    "siteconfig", "navmenu", "headerconfig", "trackingid", "gtmid", "googletagmanager",
    "analytics", "webpack", "runtimechunk", "csrftoken", "sessionid", "cookiepolicy",
    "bannerconfig", "footerlinks", "privacypolicyhtml", "widgetoptions", "portalconfig",
    "authconfig", "apiendpoint", "appversion", "environmentconfig"
]

# Primary indicators of hiring intent and recruitment language
JOB_ROLE_KEYWORDS = [
    r"\b(?:intern|internship|trainee|apprentice|engineer|developer|analyst|manager|lead)\b",
    r"\b(?:assistant|specialist|designer|director|representative|officer|technician|associate)\b",
    r"\b(?:consultant|administrator|executive|coordinator|clerk|recruiter|operator)\b",
]

JOB_RESPONSIBILITY_KEYWORDS = [
    r"\b(?:responsibilities|duties|what\s+you(?:'ll|\s+will)\s+do|key\s+tasks|day\s+to\s+day)\b",
    r"\b(?:role\s+overview|job\s+summary|you\s+will\s+be\s+responsible\s+for|collaborate\s+with)\b",
    r"\b(?:develop|build|design|maintain|support|execute|implement|deliver|manage)\b",
]

JOB_REQUIREMENT_KEYWORDS = [
    r"\b(?:requirements|qualifications|eligibility|prerequisites|candidate\s+profile)\b",
    r"\b(?:skills|experience|degree|bachelor|master|education|proficiency|must\s+have)\b",
    r"\b(?:familiarity\s+with|knowledge\s+of|years\s+of\s+experience|proficient\s+in)\b",
]

JOB_CONTEXT_KEYWORDS = [
    r"\b(?:we\s+are\s+hiring|urgently\s+hiring|immediate\s+hire|join\s+our\s+team|career\s+opportunity)\b",
    r"\b(?:job\s+posting|employment|full-time|part-time|stipend|salary|compensation|benefits|apply)\b",
]


def check_for_schema_org_job_posting(parsed_json: Any) -> Optional[Dict[str, Any]]:
    """Check if JSON represents a genuine schema.org JobPosting."""
    candidates = parsed_json if isinstance(parsed_json, list) else [parsed_json]
    for c in candidates:
        if isinstance(c, dict):
            if c.get("@type") == "JobPosting":
                return c
            if "@graph" in c and isinstance(c["@graph"], list):
                for g in c["@graph"]:
                    if isinstance(g, dict) and g.get("@type") == "JobPosting":
                        return g
    return None


def validate_job_content(text: str) -> ContentValidationResult:
    """Evaluate whether the submitted string is a genuine job posting or invalid technical text."""
    if not text or len(text.strip()) < 20:
        return ContentValidationResult(
            is_valid_job=False,
            confidence_score=0.0,
            error_message="The submitted content is too brief to evaluate. Please provide a complete job posting.",
            detected_issues=["Content length under 20 characters"],
            job_signal_score=0.0,
        )

    clean_str = text.strip()
    detected_issues: List[str] = []

    # 1. Check for JSON format
    is_json = False
    parsed_json = None
    if (clean_str.startswith("{") and clean_str.endswith("}")) or (clean_str.startswith("[") and clean_str.endswith("]")):
        try:
            parsed_json = json.loads(clean_str)
            is_json = True
        except Exception:
            pass

    # If it is valid JSON, check if it's an authentic JobPosting or website config
    if is_json and parsed_json is not None:
        schema_job = check_for_schema_org_job_posting(parsed_json)
        if schema_job:
            return ContentValidationResult(
                is_valid_job=True,
                confidence_score=0.95,
                error_message=None,
                detected_issues=[],
                job_signal_score=1.0,
            )

        # Check keys against website configuration signatures
        def flatten_keys(obj: Any, depth: int = 0) -> List[str]:
            if depth > 4 or not isinstance(obj, dict):
                return []
            keys = []
            for k, v in obj.items():
                keys.append(str(k).lower())
                if isinstance(v, dict):
                    keys.extend(flatten_keys(v, depth + 1))
            return keys

        json_keys = flatten_keys(parsed_json)
        matched_config_keys = [k for k in json_keys if any(cfg in k for cfg in TECHNICAL_CONFIG_KEYS)]

        if matched_config_keys:
            detected_issues.append(f"Identified website configuration JSON (keys: {', '.join(matched_config_keys[:4])})")
            return ContentValidationResult(
                is_valid_job=False,
                confidence_score=0.0,
                error_message=(
                    "Job Description Not Detected. The submitted content appears to contain website configuration, "
                    "portal settings, or technical metadata rather than an actual job posting. "
                    "Please paste the visible job description, including responsibilities and qualifications."
                ),
                detected_issues=detected_issues,
                job_signal_score=0.0,
            )

    # 2. Check for technical configuration regex signatures in raw text (even if invalid JSON)
    lower_text = clean_str.lower()
    config_regex_matches = re.findall(
        r'["\']?(?:themeOptions|customTheme|primary-color|varTheme|siteConfig|navMenu|trackingId|privacypolicyhtml)["\']?\s*[:=]',
        clean_str,
        re.IGNORECASE,
    )
    if len(config_regex_matches) >= 2 or re.search(r'["\']themeOptions["\']\s*:\s*\{', clean_str, re.IGNORECASE):
        detected_issues.append("Detected career portal theme/branding configuration blocks")

    # 3. Check code / syntax density
    code_chars = sum(clean_str.count(c) for c in ["{", "}", "[", "]", ";", "<", ">", "\\", "_", "="])
    total_chars = max(1, len(clean_str))
    code_density = code_chars / total_chars

    if code_density > 0.15 and not any(re.search(pat, lower_text) for pat in JOB_ROLE_KEYWORDS):
        detected_issues.append("High technical syntax density without job role keywords")

    # 4. Check for pure cookie/privacy banners or navigation menus
    cookie_matches = re.findall(r"\b(?:cookies?|privacy\s+policy|terms\s+of\s+service|tracking\s+technologies|accept\s+all)\b", lower_text)
    if len(cookie_matches) >= 4 and len(clean_str) < 1500 and not any(re.search(pat, lower_text) for pat in JOB_ROLE_KEYWORDS):
        detected_issues.append("Appears to be cookie consent or legal privacy notice rather than a job vacancy")

    # 5. Evaluate genuine job recruitment signals
    role_count = sum(1 for pat in JOB_ROLE_KEYWORDS if re.search(pat, lower_text))
    resp_count = sum(1 for pat in JOB_RESPONSIBILITY_KEYWORDS if re.search(pat, lower_text))
    req_count = sum(1 for pat in JOB_REQUIREMENT_KEYWORDS if re.search(pat, lower_text))
    context_count = sum(1 for pat in JOB_CONTEXT_KEYWORDS if re.search(pat, lower_text))

    total_signals = role_count + resp_count + req_count + context_count
    max_possible_signals = len(JOB_ROLE_KEYWORDS) + len(JOB_RESPONSIBILITY_KEYWORDS) + len(JOB_REQUIREMENT_KEYWORDS) + len(JOB_CONTEXT_KEYWORDS)
    job_signal_score = round(total_signals / max_possible_signals, 2)

    # Rejection threshold
    if detected_issues and total_signals <= 1:
        return ContentValidationResult(
            is_valid_job=False,
            confidence_score=0.0,
            error_message=(
                "Job Description Not Detected. The submitted content appears to contain website configuration, "
                "metadata, or technical code rather than an actual job posting. "
                "Please paste the visible job description, including responsibilities and qualifications."
            ),
            detected_issues=detected_issues,
            job_signal_score=job_signal_score,
        )

    # If code density is overwhelming (> 25%) and recruitment signals are missing
    if code_density > 0.22 and total_signals < 2:
        detected_issues.append("Content consists primarily of code or serialized data rather than prose")
        return ContentValidationResult(
            is_valid_job=False,
            confidence_score=0.0,
            error_message=(
                "Job Description Not Detected. The submitted content appears to contain code, scripts, or data objects "
                "rather than a readable job vacancy announcement. Please paste the visible job posting text."
            ),
            detected_issues=detected_issues,
            job_signal_score=job_signal_score,
        )

    # Valid job content confidence calculation
    confidence = 0.50  # Base for passing validation
    if role_count >= 1:
        confidence += 0.15
    if resp_count >= 1:
        confidence += 0.15
    if req_count >= 1:
        confidence += 0.10
    if context_count >= 1:
        confidence += 0.10

    return ContentValidationResult(
        is_valid_job=True,
        confidence_score=round(min(1.0, confidence), 2),
        error_message=None,
        detected_issues=detected_issues,
        job_signal_score=job_signal_score,
    )

