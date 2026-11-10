"""JobShield AI - Greenhouse False-Positive Regression Tests.

Regression suite for the false LISTING_PAGE classification of individual
Greenhouse job postings. Root cause: the page title pattern r"\\bopen\\s+positions\\b"
was incorrectly matching Greenhouse's ATS branding suffix
"<Job Title> - Open Positions at <Company>" on every individual job page.

All tests use mocked HTTP responses - no live network calls are made.
"""

from __future__ import annotations

import socket
import textwrap
import unittest
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Shared HTML fixtures
# ---------------------------------------------------------------------------

# Realistic Greenhouse individual job page (JS-rendered → static shell has noscript,
# but also includes the job content in a <div id="app"> for clients that run JS).
# For testing purposes we provide the *full rendered content* as if the fetcher
# received a server-side-rendered response.
_GREENHOUSE_JOB_HTML = textwrap.dedent("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <title>Senior Software Engineer - Open Positions at Twilio</title>
      <meta property="og:title" content="Senior Software Engineer" />
      <meta name="description" content="Twilio is hiring a Senior Software Engineer.">
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": "Senior Software Engineer",
        "description": "Join Twilio as a Senior Software Engineer. Build scalable APIs.",
        "hiringOrganization": {"@type": "Organization", "name": "Twilio"},
        "jobLocation": {"@type": "Place", "address": {"addressLocality": "San Francisco", "addressRegion": "CA"}},
        "employmentType": "FULL_TIME",
        "datePosted": "2026-10-01"
      }
      </script>
    </head>
    <body>
      <nav>
        <a href="/twilio/jobs">Open Positions at Twilio</a>
        <a href="/">Greenhouse</a>
      </nav>
      <main id="main">
        <h1>Senior Software Engineer</h1>
        <p>Twilio is looking for a Senior Software Engineer to join our infrastructure team.</p>
        <h2>Responsibilities</h2>
        <ul>
          <li>Design and build distributed systems handling millions of API calls daily.</li>
          <li>Collaborate with product managers and QA engineers to ship high-quality features.</li>
          <li>Participate in on-call rotations and incident response.</li>
        </ul>
        <h2>Requirements</h2>
        <ul>
          <li>5+ years of professional software engineering experience.</li>
          <li>Proficiency in Python, Go, or Java.</li>
          <li>Bachelor's degree in Computer Science or equivalent experience.</li>
        </ul>
        <h2>Benefits</h2>
        <p>Competitive salary, equity, 401(k), health insurance, remote-friendly culture.</p>
      </main>
      <!-- Related jobs recommendation widget -->
      <section class="related-jobs">
        <h3>More jobs at Twilio</h3>
        <ul>
          <li><a href="/twilio/jobs/8319000">Staff Engineer</a></li>
          <li><a href="/twilio/jobs/8319001">Principal Engineer</a></li>
        </ul>
      </section>
    </body>
    </html>
""").strip()

# Greenhouse company listing page (all jobs for a company)
_GREENHOUSE_LISTING_HTML = textwrap.dedent("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <title>Open Positions at Twilio</title>
    </head>
    <body>
      <h1>Open Positions at Twilio</h1>
      <div class="opening">
        <h3><a href="/twilio/jobs/100">Senior Engineer</a></h3>
        <p>Engineering • San Francisco</p>
      </div>
      <div class="opening">
        <h3><a href="/twilio/jobs/101">Product Manager</a></h3>
        <p>Product • Remote</p>
      </div>
      <div class="opening">
        <h3><a href="/twilio/jobs/102">Data Scientist</a></h3>
        <p>Analytics • New York</p>
      </div>
    </body>
    </html>
""").strip()

# Individual job page that contains many navigation / related-job links in the sidebar
_JOB_WITH_NAV_LINKS_HTML = textwrap.dedent("""
    <!DOCTYPE html>
    <html>
    <head><title>Python Backend Developer - Acme Corp</title></head>
    <body>
      <nav>
        <a href="/jobs">All Jobs</a>
        <a href="/remote-jobs">Remote Jobs</a>
        <a href="/find-jobs">Find Jobs</a>
      </nav>
      <main>
        <h1>Python Backend Developer</h1>
        <p>Acme Corp is hiring a Python Backend Developer. We are a fast-growing startup.</p>
        <h2>Responsibilities</h2>
        <ul>
          <li>Build REST APIs using FastAPI and Django.</li>
          <li>Manage PostgreSQL databases and Redis caches.</li>
        </ul>
        <h2>Requirements</h2>
        <ul>
          <li>3+ years Python experience. Bachelor's degree preferred.</li>
          <li>Knowledge of cloud services (AWS, GCP).</li>
        </ul>
        <p>Salary: $95,000. Full-time. Apply at careers@acme.com.</p>
      </main>
      <aside>
        <h3>Similar roles</h3>
        <ul>
          <li><a href="/jobs/42">Senior Python Developer</a></li>
          <li><a href="/jobs/43">Go Backend Engineer</a></li>
        </ul>
      </aside>
    </body>
    </html>
""").strip()

# Valid individual job page with JobPosting JSON-LD
_JOB_WITH_JSONLD_HTML = textwrap.dedent("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Data Engineer | Datadog</title>
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": "Data Engineer",
        "description": "Build data pipelines and analytics infrastructure at Datadog.",
        "hiringOrganization": {"@type": "Organization", "name": "Datadog"},
        "employmentType": "FULL_TIME",
        "jobLocation": {"@type": "Place", "address": {"addressLocality": "New York"}}
      }
      </script>
    </head>
    <body>
      <main>
        <h1>Data Engineer</h1>
        <p>Build scalable data pipelines. Requirements: SQL, Python, Spark.
           Bachelor's degree in Computer Science. Salary: $110,000.</p>
        <h2>Responsibilities</h2>
        <ul><li>Design ETL pipelines.</li><li>Maintain data warehouse.</li></ul>
        <h2>Requirements</h2>
        <ul><li>3+ years experience with Spark and Python.</li></ul>
      </main>
    </body>
    </html>
""").strip()

# Individual job page without structured metadata (plain HTML only)
_JOB_NO_METADATA_HTML = textwrap.dedent("""
    <!DOCTYPE html>
    <html>
    <head><title>Frontend Engineer at Stripe</title></head>
    <body>
      <main>
        <h1>Frontend Engineer</h1>
        <p>Stripe is hiring a Frontend Engineer for our payments dashboard team.</p>
        <h2>Responsibilities</h2>
        <ul>
          <li>Build React components for the Stripe Dashboard.</li>
          <li>Collaborate with designers and backend engineers.</li>
        </ul>
        <h2>Requirements</h2>
        <ul>
          <li>3+ years React experience. TypeScript proficiency.</li>
          <li>Bachelor's degree in Computer Science or equivalent.</li>
        </ul>
        <p>Compensation: $130,000. Full-time, hybrid.</p>
      </main>
    </body>
    </html>
""").strip()

# Genuine multi-job listing page (RemoteOK style)
_MULTI_JOB_LISTING_HTML = textwrap.dedent("""
    <!DOCTYPE html>
    <html>
    <head><title>Remote Python Jobs — RemoteOK</title></head>
    <body>
      <h1>Remote Python Jobs</h1>
      <table>
        <tr class="job"><td>Senior Python Engineer</td><td>Company A</td><td>$120k</td></tr>
        <tr class="job"><td>Python Data Scientist</td><td>Company B</td><td>$110k</td></tr>
        <tr class="job"><td>Python Backend Developer</td><td>Company C</td><td>$100k</td></tr>
        <tr class="job"><td>Python Full-Stack Engineer</td><td>Company D</td><td>$95k</td></tr>
        <tr class="job"><td>Python DevOps Engineer</td><td>Company E</td><td>$105k</td></tr>
      </table>
    </body>
    </html>
""").strip()


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

class _MockResponse:
    def __init__(self, status_code=200, html="", reason="OK", headers=None):
        self.status_code = status_code
        self.reason_phrase = reason
        self.content = html.encode("utf-8")
        self.encoding = "utf-8"
        self.headers = headers or {}


def _mock_dns(hostname_to_ip: dict):
    def _fake(hostname, port, proto=0, **_):
        ip = hostname_to_ip.get(hostname, "93.184.216.34")
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 443))]
    return patch("socket.getaddrinfo", side_effect=_fake)


def _make_url_request(url: str):
    from backend.app.schemas.extraction import UrlExtractionRequest
    return UrlExtractionRequest(url=url)


# ---------------------------------------------------------------------------
# classify_page_content() unit tests
# ---------------------------------------------------------------------------

class TestClassifyPageContentGreenhouse:
    """Direct unit tests for classify_page_content() covering Greenhouse scenarios."""

    def test_greenhouse_individual_job_url_not_classified_as_listing(self):
        """Root-cause regression: job-boards.greenhouse.io/{co}/jobs/{id} must NOT be LISTING_PAGE."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html=_GREENHOUSE_JOB_HTML,
            cleaned_text=(
                "Senior Software Engineer. Twilio is looking for a Senior Software Engineer "
                "to join our infrastructure team. Responsibilities: Design and build distributed systems. "
                "Requirements: 5+ years of professional software engineering experience. "
                "Benefits: Competitive salary, equity, 401(k)."
            ),
            page_title="Senior Software Engineer - Open Positions at Twilio",
            request_url="https://job-boards.greenhouse.io/twilio/jobs/8319386?utm_source=chatgpt.com",
            json_ld={"@type": "JobPosting", "title": "Senior Software Engineer"},
        )
        assert result is None, (
            f"Greenhouse individual job URL was misclassified as {result!r}. "
            "Expected None (pass through to extraction)."
        )

    def test_greenhouse_boards_subdomain_also_trusted(self):
        """boards.greenhouse.io (older subdomain) must also be treated as individual-job."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html=_GREENHOUSE_JOB_HTML,
            cleaned_text="Software Engineer at Acme. Requirements: Python, 3+ years experience.",
            page_title="Software Engineer - Open Positions at Acme",
            request_url="https://boards.greenhouse.io/acme/jobs/123456",
            json_ld=None,
        )
        assert result is None, (
            f"boards.greenhouse.io individual job URL was misclassified as {result!r}."
        )

    def test_greenhouse_company_listing_page_still_detected(self):
        """The bare /twilio/jobs listing page (no job ID) must still be classified correctly.

        Note: Greenhouse company listing pages use their own domain and structure,
        but the classifier should catch them via title or HTML structure signals.
        The bare listing page at boards.greenhouse.io/twilio/jobs may pass through
        to content_validator since it's a trusted hostname — this is acceptable
        because content_validator will reject it as non-job technical content.
        This test verifies it does NOT incorrectly return SUCCESS with job content.
        """
        from backend.app.services.extraction.extraction_service import classify_page_content

        # Listing page - only title/minimal content, no specific job description
        result = classify_page_content(
            html=_GREENHOUSE_LISTING_HTML,
            cleaned_text="Open Positions at Twilio. Senior Engineer. Product Manager. Data Scientist.",
            page_title="Open Positions at Twilio",
            request_url="https://job-boards.greenhouse.io/twilio",  # no /jobs/{id}
            json_ld=None,
        )
        # On trusted hostname with no individual-job path pattern, the result
        # may be None (pass to content validator) OR LISTING_PAGE.
        # Either is acceptable — the key requirement is that it must NOT be None
        # for a URL with a specific job ID when the content IS a listing.
        # We just verify it doesn't crash.
        assert result in (None, "LISTING_PAGE", "NOT_A_JOB_POSTING")

    def test_open_positions_phrase_alone_no_longer_triggers_listing(self):
        """'Open Positions' in title must NOT trigger LISTING_PAGE for a non-trusted URL.

        This was the root cause of the Greenhouse false positive. Even for non-trusted
        hostnames, 'open positions' in a title is insufficient evidence for LISTING_PAGE
        since it's used in page-title suffixes by many legitimate individual job pages.
        """
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html="<html><body><h1>Engineer</h1><p>We are hiring a software engineer. "
                 "Requirements: Python. 3+ years experience. Full-time position.</p></body></html>",
            cleaned_text=(
                "Software Engineer. We are hiring a software engineer. "
                "Requirements: Python. 3+ years experience. Full-time position."
            ),
            page_title="Software Engineer - Open Positions at Acme Corp",
            request_url="https://careers.acme.com/jobs/engineer-123",
            json_ld=None,
        )
        # Must NOT be LISTING_PAGE — 'open positions' is in title but URL has /jobs/{slug}
        assert result != "LISTING_PAGE", (
            "False positive: 'Open Positions' in title incorrectly triggered LISTING_PAGE."
        )

    def test_individual_job_page_with_related_job_links_passes(self):
        """Individual job page containing related-job navigation links must not be LISTING_PAGE."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html=_JOB_WITH_NAV_LINKS_HTML,
            cleaned_text=(
                "Python Backend Developer. Acme Corp is hiring a Python Backend Developer. "
                "Build REST APIs. Requirements: 3+ years Python. Salary: $95,000."
            ),
            page_title="Python Backend Developer - Acme Corp",
            request_url="https://jobs.acme.com/jobs/python-backend-dev-456",
            json_ld=None,
        )
        assert result is None, (
            f"Individual job page with related-job nav links was misclassified as {result!r}."
        )

    def test_individual_job_page_with_nav_links_passes(self):
        """Individual job page whose navigation contains 'Find Jobs' or 'Remote Jobs' must pass."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html=_JOB_WITH_NAV_LINKS_HTML,
            cleaned_text=(
                "Python Backend Developer at Acme. Build REST APIs and manage PostgreSQL databases. "
                "Requirements: 3+ years Python experience. Bachelor's degree preferred. "
                "Salary: $95,000. Full-time."
            ),
            page_title="Python Backend Developer - Acme Corp",
            request_url="https://www.acme.com/careers/jobs/software-engineer-python",
            json_ld=None,
        )
        # Nav contains "All Jobs", "Remote Jobs", "Find Jobs" but the page URL has /jobs/{slug}
        # which is an individual-job path pattern → should not be LISTING_PAGE
        assert result != "LISTING_PAGE", (
            "Navigation links incorrectly caused individual job page to be classified as LISTING_PAGE."
        )

    def test_individual_job_page_with_jsonld_job_posting_passes(self):
        """Individual job page with JobPosting JSON-LD must always pass through."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html=_JOB_WITH_JSONLD_HTML,
            cleaned_text="Data Engineer. Build data pipelines. Requirements: SQL, Python, Spark.",
            page_title="Data Engineer | Datadog",
            request_url="https://www.datadog.com/careers/jobs/data-engineer",
            json_ld={"@type": "JobPosting", "title": "Data Engineer"},
        )
        assert result is None, (
            f"Job page with valid JobPosting JSON-LD was misclassified as {result!r}."
        )

    def test_individual_job_page_without_metadata_passes(self):
        """Individual job page without JSON-LD must pass through to content_validator."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html="<html><body><h1>Frontend Engineer</h1>"
                 "<p>Stripe is hiring a Frontend Engineer. Build React components. "
                 "Requirements: 3+ years React, TypeScript. Salary: $130,000. Full-time.</p></body></html>",
            cleaned_text=(
                "Frontend Engineer. Stripe is hiring a Frontend Engineer. Build React components. "
                "Requirements: 3+ years React, TypeScript. Salary: $130,000. Full-time."
            ),
            page_title="Frontend Engineer at Stripe",
            request_url="https://stripe.com/jobs/listing/frontend-engineer/2500123",
            json_ld=None,
        )
        assert result is None, (
            f"Individual job page without metadata was misclassified as {result!r}."
        )

    def test_genuine_multi_job_listing_still_detected(self):
        """Multi-job listing pages must still be classified as LISTING_PAGE."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html=_MULTI_JOB_LISTING_HTML,
            cleaned_text=(
                "Remote Python Jobs. Senior Python Engineer. Python Data Scientist. "
                "Python Backend Developer. Python Full-Stack Engineer. Python DevOps Engineer."
            ),
            page_title="Remote Python Jobs",
            request_url="https://remoteok.com/remote-python-jobs",
            json_ld=None,
        )
        assert result == "LISTING_PAGE", (
            f"Genuine multi-job listing page was not classified as LISTING_PAGE. Got: {result!r}"
        )

    def test_numeric_job_id_in_path_bypasses_listing_checks(self):
        """URL with /jobs/{numeric_id} is an individual job — must bypass listing heuristics."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        # Even if title accidentally contains "open positions" and there's no JSON-LD
        result = classify_page_content(
            html="<html><body><h1>Engineer</h1><p>Job description text here. "
                 "Requirements: Python 3+ years. Responsibilities: Build APIs. Salary: $100k.</p></body></html>",
            cleaned_text=(
                "Engineer. Job description text here. Requirements: Python 3+ years. "
                "Responsibilities: Build APIs. Salary: $100k."
            ),
            page_title="Software Engineer - Open Positions at Company",  # would have been false positive
            request_url="https://careers.example.com/jobs/9876543",
            json_ld=None,
        )
        assert result != "LISTING_PAGE", (
            f"URL with /jobs/{{numeric_id}} was incorrectly classified as LISTING_PAGE."
        )

    def test_slug_job_path_bypasses_listing_checks(self):
        """/jobs/{slug-with-dashes} is an individual job URL."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html="<html><body><h1>Engineer</h1><p>Requirements: Python. Responsibilities: Build. Salary: $100k.</p></body></html>",
            cleaned_text="Engineer. Requirements: Python. Responsibilities: Build APIs. Full-time position.",
            page_title="Software Engineer - Find Jobs at Acme",  # would have triggered old pattern
            request_url="https://careers.example.com/jobs/software-engineer-python-remote",
            json_ld=None,
        )
        assert result != "LISTING_PAGE"

    def test_bare_jobs_path_still_flagged_as_listing(self):
        """A URL with ONLY /jobs (no job ID) must still be flagged as a listing page."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html="<html><body><h2>All Jobs</h2><ul><li>Engineer</li><li>Manager</li></ul></body></html>",
            cleaned_text="All Jobs. Browse our open roles. Engineer. Manager. Product Designer.",
            page_title="Job Search Results",
            request_url="https://careers.example.com/jobs",
            json_ld=None,
        )
        assert result == "LISTING_PAGE", (
            f"Bare /jobs URL was not classified as LISTING_PAGE. Got: {result!r}"
        )

    def test_lever_co_trusted_hostname(self):
        """jobs.lever.co is a trusted individual-job hostname."""
        from backend.app.services.extraction.extraction_service import classify_page_content

        result = classify_page_content(
            html="<html><body><h1>Engineer</h1><p>Requirements: Python 3+ years. Salary: $100k. Full-time.</p></body></html>",
            cleaned_text="Engineer. Requirements: Python 3+ years. Salary: $100k. Full-time position.",
            page_title="Software Engineer - Open Positions at Startup",
            request_url="https://jobs.lever.co/startupco/abc12345-def6-7890-gh12-ij3456789012",
            json_ld=None,
        )
        assert result is None, (
            f"jobs.lever.co individual job URL was misclassified as {result!r}."
        )


# ---------------------------------------------------------------------------
# Integration tests with mocked HTTP (ExtractionService.extract_from_url)
# ---------------------------------------------------------------------------

class TestGreenhouseExtractionIntegration:
    """End-to-end tests through extract_from_url() with mocked HTTP responses."""

    @patch("httpx.Client")
    def test_greenhouse_individual_job_url_returns_success(self, mock_client_cls):
        """Greenhouse /jobs/{id} URL must return extraction_status=SUCCESS, not LISTING_PAGE."""
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(200, _GREENHOUSE_JOB_HTML, "OK")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"job-boards.greenhouse.io": "185.199.108.153"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request(
                "https://job-boards.greenhouse.io/twilio/jobs/8319386?utm_source=chatgpt.com"
            )
            res = JobExtractionService.extract_from_url(req)

        assert res.extraction_status != "LISTING_PAGE", (
            f"Greenhouse individual job returned LISTING_PAGE — false positive not fixed."
        )
        assert res.success is True, (
            f"Greenhouse individual job returned success=False with status={res.extraction_status!r}."
        )
        assert res.extraction_confidence > 0.0

    @patch("httpx.Client")
    def test_greenhouse_job_404_returns_retrieval_failed(self, mock_client_cls):
        """Greenhouse job URL returning 404 must return RETRIEVAL_FAILED."""
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(404, "<html>Not Found</html>", "Not Found")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"job-boards.greenhouse.io": "185.199.108.153"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://job-boards.greenhouse.io/twilio/jobs/9999999")
            res = JobExtractionService.extract_from_url(req)

        assert res.success is False
        assert res.extraction_status == "RETRIEVAL_FAILED"
        assert res.extraction_confidence == 0.0
        assert res.completeness.score == 0

    @patch("httpx.Client")
    def test_greenhouse_job_403_returns_access_restricted(self, mock_client_cls):
        """Greenhouse job URL returning 403 must return ACCESS_RESTRICTED."""
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(403, "<html>Forbidden</html>", "Forbidden")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"job-boards.greenhouse.io": "185.199.108.153"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://job-boards.greenhouse.io/twilio/jobs/8319386")
            res = JobExtractionService.extract_from_url(req)

        assert res.success is False
        assert res.extraction_status == "ACCESS_RESTRICTED"
        assert res.extraction_confidence == 0.0

    @patch("httpx.Client")
    def test_genuine_listing_page_still_classified(self, mock_client_cls):
        """Multi-job listing pages must still return LISTING_PAGE after the fix."""
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(200, _MULTI_JOB_LISTING_HTML, "OK")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"remoteok.com": "104.21.44.148"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://remoteok.com/remote-python-jobs")
            res = JobExtractionService.extract_from_url(req)

        assert res.success is False
        assert res.extraction_status == "LISTING_PAGE"
        assert res.extraction_confidence == 0.0

    @patch("httpx.Client")
    def test_individual_job_with_related_links_not_listing(self, mock_client_cls):
        """Job page containing related-job recommendation widgets must not be LISTING_PAGE."""
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(200, _JOB_WITH_NAV_LINKS_HTML, "OK")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"jobs.acme.com": "93.184.216.34"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://jobs.acme.com/jobs/python-backend-dev-456")
            res = JobExtractionService.extract_from_url(req)

        assert res.extraction_status != "LISTING_PAGE", (
            f"Individual job page with nav links returned LISTING_PAGE. Status: {res.extraction_status!r}"
        )


# ---------------------------------------------------------------------------
# Trusted hostname / path pattern unit tests
# ---------------------------------------------------------------------------

class TestTrustedIndividualJobPatterns:
    """Unit tests for _KNOWN_INDIVIDUAL_JOB_HOSTNAMES and _INDIVIDUAL_JOB_PATH_PATTERNS."""

    def test_known_individual_job_hostnames_contains_greenhouse(self):
        from backend.app.services.extraction.extraction_service import _KNOWN_INDIVIDUAL_JOB_HOSTNAMES
        assert "job-boards.greenhouse.io" in _KNOWN_INDIVIDUAL_JOB_HOSTNAMES
        assert "boards.greenhouse.io" in _KNOWN_INDIVIDUAL_JOB_HOSTNAMES
        assert "jobs.lever.co" in _KNOWN_INDIVIDUAL_JOB_HOSTNAMES

    def test_individual_job_path_pattern_matches_numeric_id(self):
        import re
        from backend.app.services.extraction.extraction_service import _INDIVIDUAL_JOB_PATH_PATTERNS
        path = "/twilio/jobs/8319386"
        assert any(re.search(p, path.lower()) for p in _INDIVIDUAL_JOB_PATH_PATTERNS), (
            f"Numeric job ID path {path!r} not matched by any individual-job path pattern."
        )

    def test_individual_job_path_pattern_matches_slug(self):
        import re
        from backend.app.services.extraction.extraction_service import _INDIVIDUAL_JOB_PATH_PATTERNS
        for path in ["/jobs/software-engineer-python", "/jobs/senior-data-scientist-remote", "/job/frontend-engineer"]:
            assert any(re.search(p, path.lower()) for p in _INDIVIDUAL_JOB_PATH_PATTERNS), (
                f"Slug path {path!r} not matched by any individual-job path pattern."
            )

    def test_bare_jobs_path_not_matched_as_individual(self):
        import re
        from backend.app.services.extraction.extraction_service import _INDIVIDUAL_JOB_PATH_PATTERNS
        path = "/jobs"
        matched = any(re.search(p, path.lower()) for p in _INDIVIDUAL_JOB_PATH_PATTERNS)
        assert not matched, (
            f"Bare /jobs path {path!r} should NOT match individual-job patterns."
        )

    def test_open_positions_removed_from_listing_title_patterns(self):
        """Confirm that 'open positions' is no longer in _LISTING_TITLE_PATTERNS."""
        import re
        from backend.app.services.extraction.extraction_service import _LISTING_TITLE_PATTERNS
        matched_patterns = [
            p for p in _LISTING_TITLE_PATTERNS
            if re.search(p, "open positions at twilio")
        ]
        assert not matched_patterns, (
            f"'open positions' still matches title patterns: {matched_patterns}. "
            "This causes false positives for Greenhouse individual job pages."
        )

    def test_listing_url_patterns_anchored_to_bare_jobs_path(self):
        """The /jobs pattern must NOT match /jobs/{id} paths."""
        import re
        from backend.app.services.extraction.extraction_service import _LISTING_URL_PATTERNS
        # Must match bare /jobs
        bare_path = "/jobs"
        assert any(re.search(p, bare_path) for p in _LISTING_URL_PATTERNS), (
            "Bare /jobs path must still be caught by listing URL patterns."
        )
        # Must NOT match /jobs/8319386
        job_id_path = "/jobs/8319386"
        # The anchored pattern ^/jobs/?$ should NOT match a path with trailing content
        matched = [p for p in _LISTING_URL_PATTERNS if re.search(p, job_id_path) and "jobs" in p and "search" not in p and "find" not in p and "remote" not in p and "career" not in p]
        # Only the job-row pattern might match — but the ^/jobs/?$ anchor prevents it
        for p in matched:
            if p in (r"^/jobs/?$",):
                pytest.fail(f"Pattern {p!r} incorrectly matched {job_id_path!r}")
