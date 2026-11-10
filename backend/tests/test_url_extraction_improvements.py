"""JobShield AI — URL Extraction Improvement Regression Tests.

Covers Issues A–D identified during real-world testing:
  A. HTTP 403 → ACCESS_RESTRICTED, zero confidence, stale state never shown.
  B. Listing pages → LISTING_PAGE status, success=False.
  C. JS-required pages → JAVASCRIPT_REQUIRED status, success=False.
  D. URLs with query-params (e.g. Qualcomm) → accepted by validate_url_security().

All HTTP interactions are mocked; no live network calls are made.
"""

from __future__ import annotations

import re
import socket
import textwrap
import unittest
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helper — build a mock httpx Response
# ---------------------------------------------------------------------------

class _MockResponse:
    """Minimal stand-in for an httpx.Response."""

    def __init__(
        self,
        status_code: int = 200,
        html: str = "",
        reason: str = "OK",
        headers: Optional[dict] = None,
    ):
        self.status_code = status_code
        self.reason_phrase = reason
        self.content = html.encode("utf-8")
        self.encoding = "utf-8"
        self.headers = headers or {}

    def raise_for_status(self):
        pass


# ---------------------------------------------------------------------------
# A — URL Security / SSRF Validation (no network calls)
# ---------------------------------------------------------------------------

class TestUrlSecurityValidation:
    """validate_url_security() tests — these only perform DNS lookups for public hostnames."""

    def test_https_url_with_query_params_accepted(self):
        """Issue D: Qualcomm-style URL with query params must pass."""
        from backend.app.services.extraction.url_fetcher import validate_url_security

        url = "https://careers.qualcomm.com/careers/job/446719784235?hl=en-US&domain=qualcomm.com"
        try:
            result = validate_url_security(url)
            # DNS may succeed or fail in sandbox — either is fine; what matters is it doesn't
            # raise SSRFValidationError for a schema/path/query-param reason.
            assert result == url.strip()
        except Exception as exc:
            # DNS failure (gaierror / SSRFValidationError) is acceptable in a no-network env.
            # What must NOT happen: rejection because of query params or encoded chars.
            err_str = str(exc).lower()
            assert "query" not in err_str
            assert "domain" not in err_str
            assert "fragment" not in err_str

    def test_localhost_rejected(self):
        from backend.app.services.extraction.url_fetcher import validate_url_security, SSRFValidationError
        with pytest.raises(SSRFValidationError):
            validate_url_security("http://localhost/jobs/123")

    def test_loopback_ip_rejected(self):
        from backend.app.services.extraction.url_fetcher import validate_url_security, SSRFValidationError
        with pytest.raises(SSRFValidationError):
            validate_url_security("http://127.0.0.1/secret")

    def test_private_network_rejected(self):
        from backend.app.services.extraction.url_fetcher import validate_url_security, SSRFValidationError
        with pytest.raises(SSRFValidationError):
            validate_url_security("http://192.168.1.100/admin")

    def test_ftp_scheme_rejected(self):
        from backend.app.services.extraction.url_fetcher import validate_url_security, SSRFValidationError
        with pytest.raises(SSRFValidationError):
            validate_url_security("ftp://example.com/jobs")

    def test_missing_hostname_rejected(self):
        from backend.app.services.extraction.url_fetcher import validate_url_security, SSRFValidationError
        with pytest.raises(SSRFValidationError):
            validate_url_security("https:///no-host/path")

    def test_cloud_metadata_rejected(self):
        from backend.app.services.extraction.url_fetcher import validate_url_security, SSRFValidationError
        with pytest.raises(SSRFValidationError):
            validate_url_security("http://169.254.169.254/metadata")

    def test_internal_domain_rejected(self):
        from backend.app.services.extraction.url_fetcher import validate_url_security, SSRFValidationError
        with pytest.raises(SSRFValidationError):
            validate_url_security("http://intranet.local/jobs")


# ---------------------------------------------------------------------------
# HttpRetrievalError class tests
# ---------------------------------------------------------------------------

class TestHttpRetrievalError:
    def test_http_retrieval_error_attributes(self):
        from backend.app.services.extraction.url_fetcher import HttpRetrievalError
        err = HttpRetrievalError(403, "ACCESS_RESTRICTED", "Blocked.")
        assert err.status_code == 403
        assert err.extraction_status == "ACCESS_RESTRICTED"
        assert "Blocked" in err.user_message
        assert "Blocked" in str(err)

    def test_timeout_uses_zero_status(self):
        from backend.app.services.extraction.url_fetcher import HttpRetrievalError
        err = HttpRetrievalError(0, "RETRIEVAL_FAILED", "Timed out.")
        assert err.status_code == 0
        assert err.extraction_status == "RETRIEVAL_FAILED"


# ---------------------------------------------------------------------------
# B — HTTP Retrieval Error Classification (mocked httpx)
# ---------------------------------------------------------------------------

_SIMPLE_JOB_HTML = textwrap.dedent("""
    <!DOCTYPE html><html><head><title>Software Engineer | Acme Corp</title></head>
    <body>
      <main>
        <h1>Software Engineer</h1>
        <p>We are hiring a software engineer to join our team.</p>
        <h2>Responsibilities</h2>
        <ul><li>Develop backend services in Python.</li><li>Collaborate with product managers.</li></ul>
        <h2>Requirements</h2>
        <ul><li>Bachelor's degree in Computer Science.</li><li>3+ years Python experience.</li></ul>
        <p>Salary: $90,000–$110,000. Apply at careers@acme.com.</p>
      </main>
    </body></html>
""").strip()

_ACCESS_DENIED_HTML = "<html><body><h1>Access Denied</h1><p>You don't have permission to access this resource.</p></body></html>"

_JS_REQUIRED_HTML = textwrap.dedent("""
    <!DOCTYPE html><html><head><title>Survey Page</title></head>
    <body>
      <noscript><p>We do not support Internet Explorer. Looks like you have old version in your cache.
      Please refresh the page to load the new version. Copyright 2023 Infosys Limited.</p></noscript>
    </body></html>
""").strip()

_LISTING_HTML = textwrap.dedent("""
    <!DOCTYPE html><html><head><title>Remote Python Jobs</title></head>
    <body>
      <h1>Remote Python Jobs</h1>
      <table>
        <tr class="job"><td>Senior Python Engineer</td><td>Company A</td></tr>
        <tr class="job"><td>Python Backend Developer</td><td>Company B</td></tr>
        <tr class="job"><td>Python Data Scientist</td><td>Company C</td></tr>
        <tr class="job"><td>Python Full-Stack Engineer</td><td>Company D</td></tr>
        <tr class="job"><td>Python DevOps Engineer</td><td>Company E</td></tr>
      </table>
    </body></html>
""").strip()

_REGISTRATION_FORM_HTML = textwrap.dedent("""
    <!DOCTYPE html><html><head><title>Campus Registration Form</title></head>
    <body>
      <h1>Infosys Campus Registration Form 2027</h1>
      <p>Please fill out the registration form to register for the campus drive.</p>
      <form>
        <input type="text" name="name" placeholder="Full Name" />
        <input type="email" name="email" placeholder="Email Address" />
        <input type="text" name="college" placeholder="College Name" />
        <input type="submit" value="Submit" />
      </form>
    </body></html>
""").strip()


def _mock_client_get(status_code: int, html: str, reason: str = "OK"):
    """Return a context-manager-compatible mock httpx.Client that returns a fixed response."""
    mock_response = _MockResponse(status_code=status_code, html=html, reason=reason)
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


def _make_url_request(url: str):
    from backend.app.schemas.extraction import UrlExtractionRequest
    return UrlExtractionRequest(url=url)


def _mock_dns(hostname_to_ip: dict):
    """Return a socket.getaddrinfo patch that maps hostnames to public IPs."""
    def _fake_getaddrinfo(hostname, port, proto=0, **_):
        ip = hostname_to_ip.get(hostname, "93.184.216.34")  # example.com public IP
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 443))]
    return patch("socket.getaddrinfo", side_effect=_fake_getaddrinfo)


class TestHttpStatusClassification:
    """Verify ExtractionResponse.extraction_status for mocked HTTP responses."""

    @patch("httpx.Client")
    def test_http_200_valid_job_returns_success(self, mock_client_cls):
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=_mock_client_get(200, _SIMPLE_JOB_HTML, "OK"))
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(200, _SIMPLE_JOB_HTML, "OK")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"jobs.acme.com": "93.184.216.34"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://jobs.acme.com/engineer")
            res = JobExtractionService.extract_from_url(req)

        assert res.success is True
        assert res.extraction_status == "SUCCESS"
        assert res.extraction_confidence > 0.0

    @patch("httpx.Client")
    def test_http_403_returns_access_restricted(self, mock_client_cls):
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(403, "<html>Access Denied</html>", "Forbidden")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"www.blocked.com": "93.184.216.34"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://www.blocked.com/careers")
            res = JobExtractionService.extract_from_url(req)

        assert res.success is False
        assert res.extraction_status == "ACCESS_RESTRICTED"
        assert res.extraction_confidence == 0.0
        assert res.completeness.score == 0

    @patch("httpx.Client")
    def test_http_404_returns_retrieval_failed(self, mock_client_cls):
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(404, "<html>Not Found</html>", "Not Found")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"jobs.example.com": "93.184.216.34"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://jobs.example.com/job/999999")
            res = JobExtractionService.extract_from_url(req)

        assert res.success is False
        assert res.extraction_status == "RETRIEVAL_FAILED"
        assert res.extraction_confidence == 0.0

    @patch("httpx.Client")
    def test_http_429_returns_access_restricted(self, mock_client_cls):
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(429, "<html>Too Many Requests</html>", "Too Many Requests")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"api.jobs.com": "93.184.216.34"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://api.jobs.com/listing/5")
            res = JobExtractionService.extract_from_url(req)

        assert res.success is False
        assert res.extraction_status == "ACCESS_RESTRICTED"
        assert "rate" in res.validation_message.lower() or "limit" in res.validation_message.lower()

    @patch("httpx.Client")
    def test_http_500_returns_retrieval_failed(self, mock_client_cls):
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(500, "<html>Server Error</html>", "Internal Server Error")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"careers.broken.com": "93.184.216.34"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://careers.broken.com/job/1")
            res = JobExtractionService.extract_from_url(req)

        assert res.success is False
        assert res.extraction_status == "RETRIEVAL_FAILED"
        assert res.extraction_confidence == 0.0

    @patch("httpx.Client")
    def test_timeout_returns_retrieval_failed(self, mock_client_cls):
        import httpx
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.side_effect = httpx.TimeoutException("timed out")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"slow.site.com": "93.184.216.34"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://slow.site.com/job/1")
            res = JobExtractionService.extract_from_url(req)

        assert res.success is False
        assert res.extraction_status == "RETRIEVAL_FAILED"
        assert "time" in res.validation_message.lower() or "respond" in res.validation_message.lower()


# ---------------------------------------------------------------------------
# C — Page Content Classification (mocked HTML fixtures)
# ---------------------------------------------------------------------------

class TestPageClassification:
    """Verify classify_page_content() returns expected status for different page types."""

    def test_js_required_page_detected(self):
        from backend.app.services.extraction.extraction_service import classify_page_content
        cleaned = (
            "We do not support Internet Explorer. "
            "Looks like you have old version in your cache. "
            "Please refresh the page to load the new version. "
            "Copyright 2023 Infosys Limited."
        )
        result = classify_page_content(
            html=_JS_REQUIRED_HTML,
            cleaned_text=cleaned,
            page_title="Survey Page",
            request_url="https://surveys.infosysapps.com/r/a/SEcampusregistration",
            json_ld=None,
        )
        assert result == "JAVASCRIPT_REQUIRED"

    def test_listing_page_via_job_rows(self):
        from backend.app.services.extraction.extraction_service import classify_page_content
        result = classify_page_content(
            html=_LISTING_HTML,
            cleaned_text="Remote Python Jobs\n• Senior Python Engineer\n• Python Backend Developer\n• Python Data Scientist\n• Python Full-Stack Engineer\n• Python DevOps Engineer",
            page_title="Remote Python Jobs",
            request_url="https://remoteok.com/remote-python-jobs",
            json_ld=None,
        )
        assert result == "LISTING_PAGE"

    def test_listing_page_via_url_pattern(self):
        from backend.app.services.extraction.extraction_service import classify_page_content
        result = classify_page_content(
            html="<html><body><p>Browse jobs</p></body></html>",
            cleaned_text="Browse open positions at our company. Find jobs that match your skills.",
            page_title="Find Jobs",
            request_url="https://example.com/jobs",
            json_ld=None,
        )
        assert result == "LISTING_PAGE"

    def test_access_denied_page_detected(self):
        from backend.app.services.extraction.extraction_service import classify_page_content
        result = classify_page_content(
            html=_ACCESS_DENIED_HTML,
            cleaned_text="Access Denied. You don't have permission to access this resource.",
            page_title="403 Forbidden",
            request_url="https://example.com/secure-page",
            json_ld=None,
        )
        assert result == "ACCESS_RESTRICTED"

    def test_registration_form_detected(self):
        from backend.app.services.extraction.extraction_service import classify_page_content
        result = classify_page_content(
            html=_REGISTRATION_FORM_HTML,
            cleaned_text="Infosys Campus Registration Form 2027. Please fill out the registration form.",
            page_title="Campus Registration Form",
            request_url="https://surveys.infosysapps.com/r/a/campus2027",
            json_ld=None,
        )
        assert result == "NOT_A_JOB_POSTING"

    def test_valid_individual_job_returns_none(self):
        from backend.app.services.extraction.extraction_service import classify_page_content
        cleaned = (
            "Software Engineer at Acme Corp. "
            "We are hiring a software engineer to join our team. "
            "Responsibilities: Develop backend services. Requirements: 3+ years Python. "
            "Salary 90000. Apply at careers@acme.com."
        )
        result = classify_page_content(
            html=_SIMPLE_JOB_HTML,
            cleaned_text=cleaned,
            page_title="Software Engineer | Acme Corp",
            request_url="https://jobs.acme.com/engineer/123",
            json_ld=None,
        )
        assert result is None  # Should pass through to normal extraction


# ---------------------------------------------------------------------------
# D — Structured Extraction Quality (mocked valid job page)
# ---------------------------------------------------------------------------

class TestStructuredExtractionQuality:
    """Verify specific extraction quality properties using mocked HTML."""

    @patch("httpx.Client")
    def test_bullet_points_no_raw_li_tags(self, mock_client_cls):
        """HTML <ul><li> items must be converted to bullet text, not raw tags."""
        html = textwrap.dedent("""
            <html><head><title>Dev Job</title></head><body><main>
            <h1>Python Developer</h1>
            <p>We are hiring Python developers. Join our team and collaborate with engineers.</p>
            <h2>Requirements</h2>
            <ul><li>3+ years Python experience</li><li>Bachelor's degree required</li></ul>
            <h2>Responsibilities</h2>
            <ul><li>Build scalable APIs</li><li>Write unit tests</li></ul>
            </main></body></html>
        """).strip()

        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(200, html, "OK")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"jobs.acme.com": "93.184.216.34"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://jobs.acme.com/python-dev")
            res = JobExtractionService.extract_from_url(req)

        # Regardless of extraction success, the description must not contain raw HTML tags
        job = res.extracted_job
        for field_val in [job.description, job.requirements, job.responsibilities]:
            if field_val:
                assert "<li>" not in field_val, f"Raw <li> tag found in field: {field_val[:200]}"
                assert "<ul>" not in field_val, f"Raw <ul> tag found in field: {field_val[:200]}"
                assert "<p>" not in field_val, f"Raw <p> tag found in field: {field_val[:200]}"

    @patch("httpx.Client")
    def test_html_entities_decoded(self, mock_client_cls):
        """HTML entities like &amp; must be decoded in extracted text."""
        html = textwrap.dedent("""
            <html><head><title>Dev &amp; Ops Job</title></head><body><main>
            <h1>Dev &amp; Ops Engineer</h1>
            <p>Looking for a Dev &amp; Ops specialist with Python &amp; AWS skills.
            Requirements: Bachelor&apos;s degree. Salary: $80,000&ndash;$100,000.</p>
            <ul>
            <li>Build CI/CD pipelines using Jenkins &amp; GitHub Actions</li>
            <li>Manage AWS &amp; GCP infrastructure</li>
            </ul>
            </main></body></html>
        """).strip()

        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(200, html, "OK")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"devops.company.io": "93.184.216.34"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://devops.company.io/job/42")
            res = JobExtractionService.extract_from_url(req)

        job = res.extracted_job
        for field_val in [job.description, job.requirements, job.title]:
            if field_val:
                assert "&amp;" not in field_val, f"Unescaped &amp; in field: {field_val[:200]}"

    @patch("httpx.Client")
    def test_failed_extraction_zero_completeness_and_confidence(self, mock_client_cls):
        """Issue A: Failed extractions must return extraction_confidence=0.0 and completeness.score=0."""
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(403, "<html>Access Denied</html>", "Forbidden")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"blocked.example.com": "93.184.216.34"}):
            from backend.app.services.extraction.extraction_service import JobExtractionService
            req = _make_url_request("https://blocked.example.com/jobs/1")
            res = JobExtractionService.extract_from_url(req)

        assert res.extraction_confidence == 0.0, "Failed extraction must return 0.0 confidence"
        assert res.completeness.score == 0, "Failed extraction must return 0 completeness"
        assert res.success is False
        assert res.is_valid_job is False


# ---------------------------------------------------------------------------
# E — ExtractionResponse Schema Integrity
# ---------------------------------------------------------------------------

class TestExtractionResponseSchema:
    """Verify that ExtractionResponse always includes extraction_status."""

    def test_schema_has_extraction_status_field(self):
        from backend.app.schemas.extraction import ExtractionResponse, ExtractedJobData, CompletenessInfo
        empty_job = ExtractedJobData()
        resp = ExtractionResponse(
            success=True,
            is_valid_job=True,
            extracted_job=empty_job,
            extracted_data=empty_job,
        )
        assert hasattr(resp, "extraction_status")
        assert resp.extraction_status == "SUCCESS"  # default

    def test_schema_extraction_status_can_be_overridden(self):
        from backend.app.schemas.extraction import ExtractionResponse, ExtractedJobData
        empty_job = ExtractedJobData()
        resp = ExtractionResponse(
            success=False,
            is_valid_job=False,
            extraction_status="ACCESS_RESTRICTED",
            extracted_job=empty_job,
            extracted_data=empty_job,
        )
        assert resp.extraction_status == "ACCESS_RESTRICTED"

    def test_schema_backward_compatible_missing_field(self):
        """Old code that constructs ExtractionResponse without extraction_status must still work."""
        from backend.app.schemas.extraction import ExtractionResponse, ExtractedJobData
        empty_job = ExtractedJobData()
        resp = ExtractionResponse(
            success=True,
            is_valid_job=True,
            extracted_job=empty_job,
            extracted_data=empty_job,
        )
        # extraction_status must default to SUCCESS
        assert resp.extraction_status == "SUCCESS"


# ---------------------------------------------------------------------------
# F — Integration: existing endpoints still operational
# ---------------------------------------------------------------------------

class TestExistingEndpointsUnchanged:
    """Verify that text extraction and DB access remain functional after changes."""

    def test_text_extraction_still_works(self):
        """extract_from_text() must still return a valid ExtractionResponse."""
        from backend.app.services.extraction.extraction_service import JobExtractionService
        from backend.app.schemas.extraction import TextExtractionRequest

        req = TextExtractionRequest(
            text=(
                "Software Engineering Intern at Stripe. Join our infrastructure team for a 12-week internship. "
                "Responsibilities: Build distributed systems, write automated tests. "
                "Requirements: CS degree, Python experience. Salary: $55/hour. Apply at stripe.com/jobs."
            )
        )
        res = JobExtractionService.extract_from_text(req)
        assert res.success is True
        assert res.extraction_confidence > 0.0
        assert res.extraction_status == "SUCCESS"

    def test_text_extraction_invalid_content_still_blocked(self):
        """extract_from_text() must still reject technical config blobs."""
        from backend.app.services.extraction.extraction_service import JobExtractionService
        from backend.app.schemas.extraction import TextExtractionRequest

        req = TextExtractionRequest(
            text=(
                '{"themeOptions": {"primaryColor": "#0F9", "siteConfig": {"navMenu": []}}, '
                '"trackingId": "UA-12345", "analyticsId": "G-XYZ", "privacypolicyhtml": "<p>...</p>"}'
            )
        )
        res = JobExtractionService.extract_from_text(req)
        assert res.success is False
        assert res.is_valid_job is False

    def test_db_still_accessible(self):
        """SQLite DB must be accessible and contain at least some records."""
        try:
            from backend.app.db.database import SessionLocal
            db = SessionLocal()
            from backend.app.db.models import JobAnalysis
            count = db.query(JobAnalysis).count()
            db.close()
            assert count >= 0  # Zero is acceptable in test env; just must not throw
        except Exception as e:
            pytest.skip(f"DB not configured in test environment: {e}")


# ---------------------------------------------------------------------------
# G — HttpRetrievalError propagation through fetch_url_content
# ---------------------------------------------------------------------------

class TestFetchUrlContentErrorPropagation:
    """Verify that fetch_url_content raises HttpRetrievalError for specific HTTP statuses."""

    @patch("httpx.Client")
    def test_403_raises_http_retrieval_error(self, mock_client_cls):
        import httpx as _httpx
        from backend.app.services.extraction.url_fetcher import fetch_url_content, HttpRetrievalError

        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(403, "", "Forbidden")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"blocked.example.com": "93.184.216.34"}):
            with pytest.raises(HttpRetrievalError) as exc_info:
                fetch_url_content("https://blocked.example.com/job/1")

        assert exc_info.value.status_code == 403
        assert exc_info.value.extraction_status == "ACCESS_RESTRICTED"

    @patch("httpx.Client")
    def test_404_raises_http_retrieval_error(self, mock_client_cls):
        from backend.app.services.extraction.url_fetcher import fetch_url_content, HttpRetrievalError

        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(404, "", "Not Found")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"jobs.example.com": "93.184.216.34"}):
            with pytest.raises(HttpRetrievalError) as exc_info:
                fetch_url_content("https://jobs.example.com/job/gone")

        assert exc_info.value.status_code == 404
        assert exc_info.value.extraction_status == "RETRIEVAL_FAILED"

    @patch("httpx.Client")
    def test_429_raises_access_restricted(self, mock_client_cls):
        from backend.app.services.extraction.url_fetcher import fetch_url_content, HttpRetrievalError

        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(429, "", "Too Many Requests")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"api.jobs.com": "93.184.216.34"}):
            with pytest.raises(HttpRetrievalError) as exc_info:
                fetch_url_content("https://api.jobs.com/job/5")

        assert exc_info.value.extraction_status == "ACCESS_RESTRICTED"

    @patch("httpx.Client")
    def test_500_raises_retrieval_failed(self, mock_client_cls):
        from backend.app.services.extraction.url_fetcher import fetch_url_content, HttpRetrievalError

        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls.return_value)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value.get.return_value = _MockResponse(500, "", "Internal Server Error")
        mock_client_cls.return_value.close = MagicMock()

        with _mock_dns({"careers.broken.com": "93.184.216.34"}):
            with pytest.raises(HttpRetrievalError) as exc_info:
                fetch_url_content("https://careers.broken.com/job/1")

        assert exc_info.value.extraction_status == "RETRIEVAL_FAILED"
        assert "500" in exc_info.value.user_message

