"""JobShield AI — HTML Content Parser.

Cleans and extracts meaningful job posting text and metadata from raw HTML using BeautifulSoup,
extracting standard schema.org JobPosting JSON-LD, meta tags, and removing advertisements,
navigation bars, footers, scripts, and theme configuration blocks.
"""

from __future__ import annotations

import json
import re
from typing import Dict, Any, Tuple, Optional
from bs4 import BeautifulSoup
from backend.app.services.extraction.text_cleaner import strip_html_to_text, clean_job_text

# Tags that never contain primary job posting content
UNWANTED_TAGS = [
    "script", "style", "noscript", "iframe", "svg", "nav", "footer",
    "header", "form", "button", "input", "select", "textarea", "aside",
    "template", "meta", "link",
]

# Candidate selectors commonly used by job boards and applicant tracking systems
PRIMARY_JOB_SELECTORS = [
    "div#job-description",
    "div#jobDescriptionText",
    "div.job-description",
    "div.posting-requirements",
    "div.job__description",
    "article.job-description",
    "main#main-content",
    "div[data-testid='job-description']",
    "section.job-details",
    "article",
    "main",
]


def extract_json_ld_job_posting(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """Extract structured schema.org JobPosting data if present in HTML head/body."""
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                candidate_list = item.get("@graph", [item]) if isinstance(item, dict) else []
                for candidate in candidate_list:
                    if isinstance(candidate, dict) and candidate.get("@type") == "JobPosting":
                        return candidate
        except Exception:
            continue
    return None


def parse_job_html(html_content: str) -> Tuple[str, Dict[str, Any]]:
    """Parse raw HTML and extract clean readable job posting text and metadata."""
    if not html_content:
        return "", {"page_title": "", "meta_description": "", "targeted_selector_used": False, "json_ld_job": None}

    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Extract JSON-LD JobPosting metadata prior to tag decomposition
    json_ld = extract_json_ld_job_posting(soup)

    # 2. Extract meta tags
    meta_title = ""
    meta_desc = ""

    if soup.title and soup.title.string:
        meta_title = clean_job_text(soup.title.string)

    og_title_tag = soup.find("meta", property="og:title")
    if og_title_tag and og_title_tag.get("content"):
        meta_title = clean_job_text(og_title_tag.get("content"))

    og_desc_tag = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    if og_desc_tag and og_desc_tag.get("content"):
        meta_desc = clean_job_text(og_desc_tag.get("content"))

    # 3. Remove non-content theme blobs and code blocks (e.g. branding-data, themeOptions)
    for code_elem in soup.find_all(["code", "div", "span"], id=re.compile(r"branding|theme|config", re.IGNORECASE)):
        code_elem.decompose()

    for elem in soup.find_all(True):
        if elem.string and elem.string.strip().startswith('{"themeOptions"'):
            elem.decompose()

    # 4. Decompose unwanted script and structural tags
    for tag_name in UNWANTED_TAGS:
        for element in soup.find_all(tag_name):
            element.decompose()

    # 5. Targeted container extraction
    selected_node = None
    for selector in PRIMARY_JOB_SELECTORS:
        candidate = soup.select_one(selector)
        if candidate and len(candidate.get_text(strip=True)) > 150:
            selected_node = candidate
            break

    target_root = selected_node if selected_node is not None else (soup.body or soup)

    # 6. Extract structured text preserving headings, paragraphs, and bullets
    # First, handle line breaks and bullets in target_root
    for br in target_root.find_all(["br", "wbr"]):
        br.replace_with("\n")

    for li in target_root.find_all("li"):
        li_t = li.get_text(" ", strip=True)
        if li_t:
            if not re.match(r"^[\u2022\u25cf\u25cb\u25aa\*\-\+]\s+", li_t):
                li_t = f"• {li_t}"
            li.replace_with(f"\n{li_t}\n")
        else:
            li.decompose()

    for h in target_root.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        h_t = h.get_text(" ", strip=True)
        if h_t:
            h.replace_with(f"\n\n## {h_t}\n\n")
        else:
            h.decompose()

    for p in target_root.find_all(["p", "tr", "blockquote"]):
        p.insert_before("\n\n")
        p.insert_after("\n\n")

    raw_extracted = target_root.get_text(separator=" ")
    extracted_text = clean_job_text(raw_extracted)

    # If the targeted text is very short or missing but meta description has rich content, use it
    if len(extracted_text.strip()) < 200 and meta_desc and len(meta_desc) > len(extracted_text):
        extracted_text = clean_job_text(f"## {meta_title}\n\n{meta_desc}")

    # If JSON-LD job description exists and contains valuable HTML/text, clean and include it
    if json_ld and json_ld.get("description"):
        clean_ld_text = clean_job_text(str(json_ld["description"]))
        if len(clean_ld_text) > len(extracted_text):
            extracted_text = clean_ld_text

    metadata = {
        "page_title": meta_title,
        "meta_description": meta_desc,
        "targeted_selector_used": bool(selected_node is not None),
        "json_ld_job": json_ld,
    }

    return extracted_text, metadata
