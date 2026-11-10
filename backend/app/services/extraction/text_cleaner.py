"""JobShield AI — Text Normalizer, HTML Stripper, and Sanitizer.

Normalizes raw job post strings, standardizes unicode characters, decodes HTML entities,
converts HTML markup into clean structured text with proper paragraph breaks and bullet points,
and neutralizes prompt injection patterns to treat all posting text as untrusted data.
"""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Any, List, Optional
from bs4 import BeautifulSoup

# Tags that never contain primary job posting content
UNWANTED_HTML_TAGS = [
    "script", "style", "noscript", "iframe", "svg", "nav", "footer",
    "header", "form", "button", "input", "select", "textarea", "aside",
    "template", "meta", "link",
]

# Common prompt injection triggers to sanitize
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"system\s*prompt\s*:",
    r"you\s+are\s+now\s+(an?\s+)?unrestricted",
    r"classify\s+this\s+as\s+legitimate",
    r"pretend\s+to\s+be",
    r"bypass\s+all\s+safeties",
]


def strip_html_to_text(raw_html: str) -> str:
    """Convert raw HTML or HTML fragments into clean, readable structured text.

    Converts:
    - <p>, <div>, <section>, <article>, <h1-h6>, <tr> to readable paragraph/line breaks.
    - <li> to properly formatted bullet points ('• ...').
    - <br> to newline breaks.
    - Decodes HTML entities (&amp;, &nbsp;, &quot;, &#39;, &lt;, &gt;, etc.).
    - Strips all HTML tags without deleting the text inside them.
    - Normalizes excessive blank lines and horizontal whitespace.
    """
    if not raw_html:
        return ""

    text = str(raw_html)

    # First decode entities so escaped tags like &lt;p&gt; turn into <p>
    text = html.unescape(text)

    # Check if there are HTML tags or angle brackets
    if "<" in text and ">" in text:
        try:
            soup = BeautifulSoup(text, "html.parser")

            # 1. Remove unwanted non-content tags
            for tag in soup.find_all(UNWANTED_HTML_TAGS):
                tag.decompose()

            # 2. Convert <br> and <wbr> into newline breaks
            for br in soup.find_all(["br", "wbr"]):
                br.replace_with("\n")

            # 3. Format list items with bullet points
            for li in soup.find_all("li"):
                li_text = li.get_text(" ", strip=True)
                if li_text:
                    if not re.match(r"^[\u2022\u25cf\u25cb\u25aa\*\-\+]\s+", li_text):
                        li_text = f"• {li_text}"
                    li.replace_with(f"\n{li_text}\n")
                else:
                    li.decompose()

            # 4. Insert spacing around headings and paragraph blocks
            for block in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "blockquote", "section"]):
                block.insert_before("\n\n")
                block.insert_after("\n\n")

            # Extract full text
            text = soup.get_text(separator=" ")

        except Exception:
            pass

        # Clean any remaining rogue or malformed HTML tags (e.g., </p>, </b> without match)
        text = re.sub(r"<[^>]+>", " ", text)

        # Re-decode in case nested entities were revealed
        text = html.unescape(text)

    return text


def clean_job_text(raw_text: str) -> str:
    """Clean, normalize, strip HTML, and sanitize raw job description text."""
    if not raw_text:
        return ""

    # Strip HTML tags and decode entities first
    text = strip_html_to_text(raw_text)

    # Normalize unicode to NFKC
    normalized = unicodedata.normalize("NFKC", text)

    # Standardize common typographic symbols
    normalized = (
        normalized.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "--")
        .replace("\u00a0", " ")
    )

    # Remove non-printable control characters (except newline, tab, carriage return)
    normalized = "".join(
        ch for ch in normalized
        if ch in ("\n", "\t", "\r") or unicodedata.category(ch)[0] != "C"
    )

    # Neutralize prompt injection phrases by defanging them
    for pattern in INJECTION_PATTERNS:
        normalized = re.sub(pattern, "[DEFANGED_PROMPT_INJECTION_ATTEMPT]", normalized, flags=re.IGNORECASE)

    # Normalize line breaks and horizontal whitespace
    lines = normalized.split("\n")
    cleaned_lines = []
    for line in lines:
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        cleaned_lines.append(cleaned)

    # Collapse consecutive blank lines into at most one blank line (\n\n)
    res_lines: List[str] = []
    last_empty = False
    for l in cleaned_lines:
        if l:
            res_lines.append(l)
            last_empty = False
        elif not last_empty:
            res_lines.append("")
            last_empty = True

    return "\n".join(res_lines).strip()


def clean_job_field(val: Optional[str]) -> Optional[str]:
    """Clean a single extracted text field ensuring no raw HTML, entities, or excess whitespace."""
    if val is None:
        return None
    cleaned = clean_job_text(str(val))
    return cleaned if cleaned else None


def clean_extracted_job_fields(job_data: Any) -> Any:
    """Apply consistent HTML and entity cleaning to every text field of an extracted job data object."""
    if job_data is None:
        return None

    string_fields = [
        "title", "company_name", "company_profile", "company_description",
        "location", "work_arrangement", "duration", "employment_type",
        "salary_range", "compensation", "required_experience", "required_education",
        "responsibilities", "requirements", "benefits", "application_instructions",
        "contact_email", "contact_phone", "contact_info", "application_url",
        "fee_details", "description"
    ]

    for field in string_fields:
        if hasattr(job_data, field):
            val = getattr(job_data, field)
            if val and isinstance(val, str):
                setattr(job_data, field, clean_job_field(val))

    if hasattr(job_data, "required_skills") and job_data.required_skills:
        job_data.required_skills = [
            clean_job_field(s) for s in job_data.required_skills if clean_job_field(s)
        ]

    if hasattr(job_data, "suspicious_claims") and job_data.suspicious_claims:
        job_data.suspicious_claims = [
            clean_job_field(c) for c in job_data.suspicious_claims if clean_job_field(c)
        ]

    return job_data
