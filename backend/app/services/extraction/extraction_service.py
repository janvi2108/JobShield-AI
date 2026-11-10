"""JobShield AI — Extraction Service Orchestrator.

High-level interface coordinating URL fetching, HTML parsing, text sanitation,
structured attribute extraction, and schema normalization into canonical response contracts.
"""

from __future__ import annotations

import re
import time
import logging
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.schemas.extraction import (
    ExtractedJobData,
    ExtractionResponse,
    CompletenessInfo,
    UrlExtractionRequest,
    TextExtractionRequest,
)
from backend.app.services.extraction.url_fetcher import fetch_url_content, SSRFValidationError, HttpRetrievalError
from backend.app.services.extraction.html_parser import parse_job_html
from backend.app.services.extraction.text_cleaner import clean_job_text, clean_extracted_job_fields
from backend.app.services.extraction.llm_extractor import extract_with_llm
from backend.app.services.extraction.normalizer import evaluate_completeness
from backend.app.services.extraction.content_validator import validate_job_content

logger = logging.getLogger("jobshield.extraction.service")


# ---------------------------------------------------------------------------
# Page content classifier — returns an extraction_status string or None
# when the page appears to be a valid job posting and normal flow should proceed.
# ---------------------------------------------------------------------------

# JS-fallback / browser-not-supported patterns (case-insensitive)
_JS_REQUIRED_PATTERNS = [
    r"we\s+do\s+not\s+support\s+internet\s+explorer",
    r"please\s+use\s+(the\s+)?(latest|updated)\s+(version|browser)",
    r"looks\s+like\s+you\s+have\s+(an?\s+)?old\s+version\s+(in\s+your\s+cache|of\s+your\s+browser)",
    r"please\s+refresh\s+the\s+page\s+to\s+load\s+the\s+new\s+version",
    r"enable\s+javascript\s+(to\s+(view|use|access)|in\s+your\s+browser)",
    r"javascript\s+is\s+required\s+to\s+view\s+this\s+(page|site|content)",
    r"this\s+(page|site|application)\s+requires\s+javascript",
    r"your\s+browser\s+does\s+not\s+support\s+javascript",
]

# Access-denied signals in page body (case-insensitive)
_ACCESS_DENIED_PATTERNS = [
    r"\baccess\s+denied\b",
    r"\b403\s+forbidden\b",
    r"\byou\s+don'?t\s+have\s+permission\b",
    r"\bcloudflare\s+ray\s+id\b",
    r"\bplease\s+(complete\s+)?(the\s+)?captcha\b",
    r"\bare\s+you\s+a\s+robot\b",
    r"\bverify\s+you\s+are\s+human\b",
]

# Job-listing page detection — URL patterns matched against the URL *path only*
_LISTING_URL_PATTERNS = [
    r"^/jobs/?$",           # bare /jobs or /jobs/  — no trailing ID
    r"/job-search",
    r"/careers/search",
    r"/remote-jobs",
    r"/find-jobs",
    r"/search/jobs",
]

_LISTING_TITLE_PATTERNS = [
    r"\bjobs?\s+listing",
    r"\bsearch\s+results\b",
    r"\bfind\s+jobs?\b",
    r"\bremote\s+jobs?\b",
    r"\bjob\s+search\b",
    # NOTE: "\bopen\s+positions\b" intentionally omitted — Greenhouse and other ATS
    # platforms append "Open Positions at <Company>" to every *individual* job page title,
    # making this pattern a reliable false-positive source.
]

# ---------------------------------------------------------------------------
# Individual job URL detection — trusted signals that override listing checks
# ---------------------------------------------------------------------------

# Well-known ATS / job-board hostnames where the URL structure
# /{company}/jobs/{id} always refers to a single job posting.
_KNOWN_INDIVIDUAL_JOB_HOSTNAMES = frozenset({
    "job-boards.greenhouse.io",
    "boards.greenhouse.io",
    "jobs.lever.co",
    "app.jobvite.com",
    "boards.eu.greenhouse.io",
})

# Path patterns that reliably indicate an individual job posting.
# Match: /jobs/8319386  /jobs/software-engineer-at-acme  /job/12345  /posting/abc-def
_INDIVIDUAL_JOB_PATH_PATTERNS = [
    r"/jobs/\d+",                   # /jobs/{numeric_id}
    r"/jobs/[a-z0-9][a-z0-9_-]{4,}",  # /jobs/{slug} — min 5 chars to avoid bare /jobs/
    r"/job/\d+",                    # /job/{numeric_id}
    r"/job/[a-z0-9][a-z0-9_-]{4,}", # /job/{slug}
    r"/posting/[a-z0-9_-]+",        # Lever-style
    r"/apply/[a-z0-9_-]+",          # Apply URLs
    r"/position/[a-z0-9_-]+",       # /position/{id}
    r"/opening/[a-z0-9_-]+",        # /opening/{id}
]

# Registration/application-form page patterns
_FORM_PAGE_PATTERNS = [
    r"\bregistration\s+form\b",
    r"\bapplication\s+form\b",
    r"\bsurvey\s+(form|page)\b",
    r"\bplease\s+fill\s+(in|out)\s+(the\s+)?(form|survey)\b",
]


def _build_failed_response(
    extraction_status: str,
    validation_message: str,
    invalid_signals: List[str],
    source_url: str,
    raw_html_len: int,
    start_time: float,
) -> ExtractionResponse:
    """Return a failure ExtractionResponse with zero confidence and completeness."""
    empty_job = ExtractedJobData()
    missing = ["title", "company_name", "location", "description", "requirements", "responsibilities"]
    empty_job.missing_fields = missing
    empty_job.completeness_score = 0.0
    return ExtractionResponse(
        success=False,
        is_valid_job=False,
        extraction_status=extraction_status,
        validation_message=validation_message,
        invalid_signals=invalid_signals,
        source_type="url",
        extraction_method="url",
        source_identifier=source_url,
        extracted_job=empty_job,
        extracted_data=empty_job,
        completeness=CompletenessInfo(score=0, missing_fields=missing),
        extraction_confidence=0.0,
        raw_character_count=raw_html_len,
        cleaned_character_count=0,
        warnings=invalid_signals,
        extraction_time_seconds=round(time.time() - start_time, 2),
    )


def classify_page_content(
    html: str,
    cleaned_text: str,
    page_title: str,
    request_url: str,
    json_ld: Optional[Dict[str, Any]],
) -> Optional[str]:
    """Classify page content and return an extraction_status string if the page is NOT a valid individual job posting.

    Returns None when the page should proceed through normal extraction logic.
    Returns a status string (e.g. 'JAVASCRIPT_REQUIRED', 'LISTING_PAGE', 'ACCESS_RESTRICTED',
    'NOT_A_JOB_POSTING') when the page fails pre-extraction classification.

    Design principle: prefer false negatives over false positives. When in doubt, pass the page
    through to the content validator so the user gets a meaningful partial result rather than
    a blanket rejection. Only fire LISTING_PAGE when there is *strong* evidence that the
    primary page content represents multiple vacancies.
    """
    from urllib.parse import urlparse as _urlparse

    lower_text = cleaned_text.lower()
    lower_title = (page_title or "").lower()

    # Parse URL components for precise path/hostname checks
    try:
        _parsed_url = _urlparse(request_url)
        url_hostname = (_parsed_url.hostname or "").lower()
        url_path = (_parsed_url.path or "").lower()
    except Exception:
        url_hostname = ""
        url_path = request_url.lower()

    # ------------------------------------------------------------------
    # FAST-PASS: trusted individual-job URL signals
    # If the hostname is a known single-job ATS platform OR the URL path
    # matches a specific job-ID pattern, skip all listing-page heuristics.
    # This prevents Greenhouse "Open Positions at X" page titles, related-job
    # navigation links, and job-row recommendation widgets from being
    # misclassified as listing pages.
    # ------------------------------------------------------------------
    is_trusted_individual_job = (
        url_hostname in _KNOWN_INDIVIDUAL_JOB_HOSTNAMES
        or any(re.search(p, url_path) for p in _INDIVIDUAL_JOB_PATH_PATTERNS)
    )

    # 1. JavaScript-required / browser-not-supported fallback pages
    for pat in _JS_REQUIRED_PATTERNS:
        if re.search(pat, lower_text):
            return "JAVASCRIPT_REQUIRED"

    # Detect noscript-dominant pages: very short cleaned text with JS-fallback phrase
    if len(cleaned_text.strip()) < 400:
        if re.search(r"noscript", html.lower()) and len(html) > 2000:
            # Page has lots of raw HTML but almost no readable text → JS-rendered
            return "JAVASCRIPT_REQUIRED"

    # 2. Access-denied signals in body content (HTTP 200 but anti-bot page)
    for pat in _ACCESS_DENIED_PATTERNS:
        if re.search(pat, lower_text):
            return "ACCESS_RESTRICTED"

    # 3. JSON-LD @type indicates non-job structured data (ItemList, BreadcrumbList, etc.)
    #    Skip this check for trusted individual-job URLs — they may legitimately embed
    #    BreadcrumbList alongside a JobPosting in the same JSON-LD block.
    if not is_trusted_individual_job:
        if json_ld is not None and isinstance(json_ld, dict):
            ld_type = json_ld.get("@type", "")
            if isinstance(ld_type, str) and ld_type not in ("JobPosting",):
                if ld_type in ("ItemList", "BreadcrumbList", "WebPage", "SearchResultsPage"):
                    return "LISTING_PAGE"

    has_jsonld_job = json_ld is not None and isinstance(json_ld, dict) and json_ld.get("@type") == "JobPosting"

    # If a confirmed JobPosting JSON-LD is present, it's definitively an individual job page.
    if has_jsonld_job:
        # Skip all remaining listing-page heuristics — JSON-LD is authoritative.
        pass
    else:
        # 4. Multiple job-row patterns in raw HTML (listing page)
        #    Only fire if NOT a trusted individual-job URL — individual job pages can contain
        #    recommendation widgets ("More jobs at Twilio") with job rows in the page sidebar.
        if not is_trusted_individual_job:
            job_row_hits = sum([
                len(re.findall(r'<tr[^>]+class=["\'][^"\']*\bjob\b', html, re.IGNORECASE)),
                len(re.findall(r'<article[^>]+class=["\'][^"\']*\bjob\b', html, re.IGNORECASE)),
                len(re.findall(r'<div[^>]+class=["\'][^"\']*\bjob[-_]card\b', html, re.IGNORECASE)),
                len(re.findall(r'<li[^>]+class=["\'][^"\']*\bjob[-_]item\b', html, re.IGNORECASE)),
            ])
            if job_row_hits >= 4:
                return "LISTING_PAGE"

        # 5. URL path / title listing heuristics
        #    Gate on is_trusted_individual_job — trusted URLs are definitively single-job pages
        #    regardless of generic title language.
        if not is_trusted_individual_job:
            # Check path-only (not full URL with query string) against listing URL patterns
            for pat in _LISTING_URL_PATTERNS:
                if re.search(pat, url_path):
                    return "LISTING_PAGE"
            for pat in _LISTING_TITLE_PATTERNS:
                if re.search(pat, lower_title):
                    return "LISTING_PAGE"

    # 6. Registration/survey/application form detection (no job-role content)
    for pat in _FORM_PAGE_PATTERNS:
        if re.search(pat, lower_text) or re.search(pat, lower_title):
            # Only classify as NOT_A_JOB_POSTING if the job content signals are thin
            from backend.app.services.extraction.content_validator import (
                JOB_ROLE_KEYWORDS, JOB_RESPONSIBILITY_KEYWORDS,
            )
            role_hits = sum(1 for p in JOB_ROLE_KEYWORDS if re.search(p, lower_text))
            resp_hits = sum(1 for p in JOB_RESPONSIBILITY_KEYWORDS if re.search(p, lower_text))
            if role_hits + resp_hits < 2:
                return "NOT_A_JOB_POSTING"

    return None  # Page passes classification — proceed normally


def compute_dynamic_confidence(job: ExtractedJobData, signal_score: float = 0.5) -> float:
    """Calculate dynamic confidence score based on populated fields and their quality."""
    weights = 0.0
    if job.title and len(job.title.strip()) >= 3:
        weights += 0.25
    if job.company_name and len(job.company_name.strip()) >= 2:
        weights += 0.15
    if job.description and len(job.description.strip()) >= 80:
        weights += 0.25
    if job.requirements and len(job.requirements.strip()) >= 20:
        weights += 0.12
    if job.responsibilities and len(job.responsibilities.strip()) >= 20:
        weights += 0.10
    if job.location and len(job.location.strip()) >= 2:
        weights += 0.05
    if job.employment_type and len(job.employment_type.strip()) >= 3:
        weights += 0.05
    if job.salary_range or job.benefits or (job.required_skills and len(job.required_skills) > 0):
        weights += 0.03

    # Blend field presence (70%) with recruitment language density (30%)
    dynamic_conf = (weights * 0.70) + (min(1.0, max(0.1, signal_score)) * 0.30)
    return round(min(0.99, max(0.05, dynamic_conf)), 2)


class JobExtractionService:
    """Unified extraction orchestrator for URLs and pasted text."""

    @staticmethod
    def extract_from_url(request: UrlExtractionRequest) -> ExtractionResponse:
        start_time = time.time()
        warnings: List[str] = []

        # --- Fetch HTML content ---
        raw_html: str = ""
        resolved_url: str = request.url

        try:
            raw_html, resolved_url = fetch_url_content(request.url)
        except SSRFValidationError as e:
            logger.warning(f"SSRF validation blocked request for URL {request.url}: {e}")
            return _build_failed_response(
                extraction_status="URL_INVALID",
                validation_message=(
                    f"The URL was blocked for security reasons: {e}. "
                    "Only publicly accessible HTTP/HTTPS URLs are supported."
                ),
                invalid_signals=["SSRF / private-network URL"],
                source_url=request.url,
                raw_html_len=0,
                start_time=start_time,
            )
        except HttpRetrievalError as e:
            logger.warning(f"HTTP retrieval error for URL {request.url}: status={e.status_code} status_str={e.extraction_status}")
            return _build_failed_response(
                extraction_status=e.extraction_status,
                validation_message=e.user_message,
                invalid_signals=[f"HTTP {e.status_code}" if e.status_code else "Network error"],
                source_url=request.url,
                raw_html_len=0,
                start_time=start_time,
            )
        except Exception as e:
            logger.error(f"Failed to fetch content from URL {request.url}: {e}")
            return _build_failed_response(
                extraction_status="RETRIEVAL_FAILED",
                validation_message=(
                    "Could not retrieve the webpage. The site may be temporarily unavailable. "
                    "Please verify the URL or paste the job description text directly."
                ),
                invalid_signals=["Network or retrieval error"],
                source_url=request.url,
                raw_html_len=0,
                start_time=start_time,
            )

        parsed_text, meta = parse_job_html(raw_html)
        cleaned_text = clean_job_text(parsed_text)

        # Supplement fields from JSON-LD schema.org JobPosting if available
        json_ld = meta.get("json_ld_job")
        has_schema_job = bool(json_ld and isinstance(json_ld, dict) and json_ld.get("title"))
        page_title = meta.get("page_title", "")

        # --- Page content pre-classification ---
        page_status = classify_page_content(
            html=raw_html,
            cleaned_text=cleaned_text,
            page_title=page_title,
            request_url=resolved_url,
            json_ld=json_ld,
        )

        if page_status is not None:
            status_messages = {
                "JAVASCRIPT_REQUIRED": (
                    "This webpage requires JavaScript to display its content. "
                    "The automated extractor cannot render JavaScript-based pages. "
                    "Please open the URL in your browser, copy the job description text, "
                    "and use the 'Paste Job Description' tab instead."
                ),
                "LISTING_PAGE": (
                    "This URL appears to contain multiple job listings rather than one individual job posting. "
                    "Please open the listing, click on a specific job title, and provide its direct URL."
                ),
                "ACCESS_RESTRICTED": (
                    "Website access was restricted. The page content indicates this site uses anti-bot protection. "
                    "Please copy and paste the job description text directly."
                ),
                "NOT_A_JOB_POSTING": (
                    "The retrieved webpage does not appear to be an individual job advertisement. "
                    "It may be a registration form, survey, or general careers page. "
                    "Please provide a direct link to a specific job posting."
                ),
            }
            msg = status_messages.get(page_status, "The retrieved page does not contain a recognizable job posting.")
            logger.info(f"Page classified as {page_status} for URL {resolved_url}")
            return _build_failed_response(
                extraction_status=page_status,
                validation_message=msg,
                invalid_signals=[f"Page type: {page_status}"],
                source_url=resolved_url,
                raw_html_len=len(raw_html),
                start_time=start_time,
            )

        # --- Validate content: ensure it's not arbitrary technical website code/config ---
        val_result = validate_job_content(cleaned_text)
        if not val_result.is_valid_job and not has_schema_job:
            return _build_failed_response(
                extraction_status="NOT_A_JOB_POSTING",
                validation_message=(
                    val_result.error_message
                    or "No valid job posting content could be detected on the target webpage."
                ),
                invalid_signals=val_result.detected_issues or ["Page content lacks recruitment signals"],
                source_url=resolved_url,
                raw_html_len=len(raw_html),
                start_time=start_time,
            )

        if len(cleaned_text) < 50:
            warnings.append("Page text was unusually short. The page might rely on dynamic client-side rendering.")

        extracted_data = extract_with_llm(cleaned_text)

        if json_ld and isinstance(json_ld, dict):
            if not extracted_data.title and json_ld.get("title"):
                extracted_data.title = str(json_ld["title"]).strip()[:200]

            if not extracted_data.company_name and json_ld.get("hiringOrganization"):
                org = json_ld["hiringOrganization"]
                extracted_data.company_name = (
                    org.get("name", "") if isinstance(org, dict) else str(org)
                ).strip()[:150]

            if not extracted_data.location and json_ld.get("jobLocation"):
                loc = json_ld["jobLocation"]
                if isinstance(loc, list) and loc:
                    loc = loc[0]
                if isinstance(loc, dict) and "address" in loc:
                    addr = loc["address"]
                    if isinstance(addr, dict):
                        locality = addr.get("addressLocality")
                        region = addr.get("addressRegion")
                        extracted_data.location = (
                            f"{locality}, {region}" if locality and region else (locality or region)
                        )

            if not extracted_data.employment_type and json_ld.get("employmentType"):
                extracted_data.employment_type = str(json_ld["employmentType"]).replace("_", " ").title()

        # Supplement title and company from page meta title if still missing
        if page_title:
            if not extracted_data.title:
                if " | " in page_title:
                    parts = page_title.split(" | ")
                    extracted_data.title = parts[0].strip()[:200]
                    if not extracted_data.company_name and len(parts) > 1:
                        extracted_data.company_name = parts[1].strip()[:150]
                elif " - " in page_title:
                    parts = page_title.split(" - ")
                    extracted_data.title = parts[0].strip()[:200]
                    if not extracted_data.company_name and len(parts) > 1:
                        extracted_data.company_name = parts[1].strip()[:150]
                else:
                    extracted_data.title = page_title.strip()[:200]
            elif not extracted_data.company_name and " | " in page_title:
                parts = page_title.split(" | ")
                if len(parts) > 1:
                    extracted_data.company_name = parts[1].strip()[:150]

        # Ensure description is populated
        if not extracted_data.description:
            extracted_data.description = cleaned_text if len(cleaned_text) > 0 else (meta.get("meta_description") or "")

        # Apply thorough HTML tag stripping and entity normalization to all extracted fields
        clean_extracted_job_fields(extracted_data)

        # Calculate completeness
        score_ratio, missing = evaluate_completeness(extracted_data)
        extracted_data.completeness_score = score_ratio
        extracted_data.missing_fields = missing
        completeness_info = CompletenessInfo(
            score=int(round(score_ratio * 100)),
            missing_fields=missing,
        )

        signal_score = 0.95 if has_schema_job else val_result.confidence_score
        dyn_conf = compute_dynamic_confidence(extracted_data, signal_score)

        elapsed = round(time.time() - start_time, 2)
        return ExtractionResponse(
            success=True,
            is_valid_job=True,
            extraction_status="SUCCESS",
            validation_message=None,
            invalid_signals=[],
            source_type="url",
            extraction_method="url",
            source_identifier=resolved_url,
            extracted_job=extracted_data,
            extracted_data=extracted_data,
            completeness=completeness_info,
            extraction_confidence=dyn_conf,
            raw_character_count=len(raw_html),
            cleaned_character_count=len(cleaned_text),
            warnings=warnings,
            extraction_time_seconds=elapsed,
        )

    @staticmethod
    def extract_from_text(request: TextExtractionRequest) -> ExtractionResponse:
        start_time = time.time()
        warnings: List[str] = []

        # Validate content before extraction
        val_result = validate_job_content(request.text)
        if not val_result.is_valid_job:
            elapsed = round(time.time() - start_time, 2)
            empty_job = ExtractedJobData()
            missing = ["title", "company_name", "location", "description", "requirements", "responsibilities"]
            empty_job.missing_fields = missing
            empty_job.completeness_score = 0.0

            return ExtractionResponse(
                success=False,
                is_valid_job=False,
                validation_message=val_result.error_message,
                invalid_signals=val_result.detected_issues,
                source_type="text",
                extraction_method="text",
                source_identifier=request.text[:120] + ("..." if len(request.text) > 120 else ""),
                extracted_job=empty_job,
                extracted_data=empty_job,
                completeness=CompletenessInfo(score=0, missing_fields=missing),
                extraction_confidence=0.0,
                raw_character_count=len(request.text),
                cleaned_character_count=0,
                warnings=val_result.detected_issues,
                extraction_time_seconds=elapsed,
            )

        cleaned_text = clean_job_text(request.text)

        if len(cleaned_text) < 40:
            warnings.append("Pasted text is brief. Providing more detail yields higher analysis accuracy.")

        extracted_data = extract_with_llm(cleaned_text)

        if not extracted_data.description:
            extracted_data.description = cleaned_text

        # Apply thorough HTML tag stripping and entity normalization to all extracted fields
        clean_extracted_job_fields(extracted_data)

        # Calculate completeness
        score_ratio, missing = evaluate_completeness(extracted_data)
        extracted_data.completeness_score = score_ratio
        extracted_data.missing_fields = missing
        completeness_info = CompletenessInfo(
            score=int(round(score_ratio * 100)),
            missing_fields=missing,
        )

        dyn_confidence = compute_dynamic_confidence(extracted_data, val_result.confidence_score)

        elapsed = round(time.time() - start_time, 2)
        snippet = cleaned_text[:120] + ("..." if len(cleaned_text) > 120 else "")

        return ExtractionResponse(
            success=True,
            is_valid_job=True,
            validation_message=None,
            invalid_signals=[],
            source_type="text",
            extraction_method="text",
            source_identifier=snippet,
            extracted_job=extracted_data,
            extracted_data=extracted_data,
            completeness=completeness_info,
            extraction_confidence=dyn_confidence,
            raw_character_count=len(request.text),
            cleaned_character_count=len(cleaned_text),
            warnings=warnings,
            extraction_time_seconds=elapsed,
        )


extraction_service = JobExtractionService()
