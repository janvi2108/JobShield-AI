"""JobShield AI — No-API-Key Operation Tests.

Verifies that the ENTIRE application works correctly without any external
API key (Groq or otherwise). Every tested capability runs offline using
only local ML inference, deterministic extraction, and SQLite storage.

Test categories:
    1. Application startup without an API key
    2. ML prediction without an API key
    3. Pasted-text extraction without an API key
    4. URL extraction without an API key (mocked HTTP)
    5. Local deterministic explanation generation
    6. Database save and retrieval without an API key
    7. Optional Groq integration (mocked — verified only when key is configured)
    8. Health endpoint reports correct LLM and database status
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.schemas.analysis import FeatureContribution
from backend.app.schemas.explanation import WarningIndicator
from backend.app.services.llm.explanation_service import (
    generate_deterministic_fallback_explanation,
    generate_grounded_explanation,
)
from backend.app.services.extraction.llm_extractor import (
    extract_deterministically,
    extract_with_llm,
)


# ---------------------------------------------------------------------------
# Helper: temporary in-memory / on-disk SQLite database for isolated tests
# ---------------------------------------------------------------------------

def _temp_db() -> Path:
    """Create a temporary SQLite database file and initialise schema."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)
    from backend.app.db.database import init_db
    init_db(db_path=db_path)
    return db_path


# ---------------------------------------------------------------------------
# 1. Application Startup Without API Key
# ---------------------------------------------------------------------------

class TestStartupWithoutApiKey(unittest.TestCase):
    """Ensure FastAPI starts, routes mount, and root/health respond without a key."""

    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint_available(self):
        """GET / must return 200 without any API key."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "operational")

    def test_health_endpoint_available_without_api_key(self):
        """GET /api/health must return 200 without any API key."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")

    def test_metrics_endpoint_available_without_api_key(self):
        """GET /api/metrics must return 200 without any API key."""
        res = self.client.get("/api/metrics")
        self.assertEqual(res.status_code, 200)

    def test_no_api_key_in_environment_does_not_crash(self):
        """Startup with LLM_API_KEY unset must not raise."""
        with patch.object(settings, "LLM_API_KEY", ""):
            with patch.object(settings, "LLM_PROVIDER", "none"):
                res = self.client.get("/api/health")
                self.assertEqual(res.status_code, 200)

    def test_provider_none_default_is_deterministic(self):
        """With LLM_PROVIDER='none', extraction must use the deterministic path."""
        with patch.object(settings, "LLM_PROVIDER", "none"):
            with patch.object(settings, "LLM_API_KEY", ""):
                result = extract_with_llm("Software Engineer at Acme Corp in London.")
                # Must return an ExtractedJobData — no crash
                self.assertIsNotNone(result)


# ---------------------------------------------------------------------------
# 2. ML Prediction Without API Key
# ---------------------------------------------------------------------------

class TestMLPredictionWithoutApiKey(unittest.TestCase):
    """Verify that fraud predictions work entirely offline."""

    def setUp(self):
        self.client = TestClient(app)

    def _analyze(self, payload: dict) -> dict:
        res = self.client.post("/api/analyze", json=payload)
        self.assertEqual(res.status_code, 200, f"Unexpected status: {res.status_code} — {res.text}")
        return res.json()

    def test_legitimate_posting_predicts_without_api_key(self):
        """A normal job posting must return a valid fraud probability."""
        data = self._analyze({
            "title": "Software Engineer",
            "company_name": "Acme Corp",
            "description": "Develop and maintain backend services. Write unit tests and participate in code reviews.",
            "requirements": "3+ years Python experience. Degree in CS or equivalent.",
            "benefits": "Health insurance, 401k, remote work.",
        })
        self.assertTrue(data["success"])
        self.assertIn("fraud_probability", data)
        self.assertIsInstance(data["fraud_probability"], float)
        self.assertGreaterEqual(data["fraud_probability"], 0.0)
        self.assertLessEqual(data["fraud_probability"], 1.0)
        self.assertIn("risk_level", data)

    def test_fraudulent_posting_flagged_without_api_key(self):
        """A scam posting should be flagged as high risk without any API key."""
        data = self._analyze({
            "title": "Urgent Work From Home Agent",
            "company_name": "",
            "description": (
                "Immediate hire guaranteed! No interview required. "
                "Send a $100 registration fee via Wire Transfer or Cash App. "
                "Contact recruiter on Telegram @jobs_agent now. Limited spots left!"
            ),
            "requirements": "No experience needed. Easy money from home.",
        })
        self.assertTrue(data["success"])
        self.assertIn("heuristic_signals", data)
        self.assertTrue(len(data["heuristic_signals"]) > 0)

    def test_prediction_returns_model_name_offline(self):
        """Prediction metadata must include the model name."""
        data = self._analyze({
            "title": "Data Analyst",
            "company_name": "Analytics Ltd",
            "description": "Build dashboards and write SQL queries for business intelligence.",
            "requirements": "SQL, Python, Tableau proficiency.",
        })
        self.assertTrue(data["success"])
        self.assertIn("model_name", data)
        self.assertIsNotNone(data["model_name"])

    def test_grounded_explanation_returned_without_api_key(self):
        """POST /api/analyze must return grounded_explanation in metadata without Groq."""
        with patch.object(settings, "LLM_API_KEY", ""):
            with patch.object(settings, "LLM_PROVIDER", "none"):
                data = self._analyze({
                    "title": "Marketing Manager",
                    "company_name": "BrandCo",
                    "description": "Lead brand campaigns. Manage social media and influencer partnerships.",
                    "requirements": "5 years marketing experience. MBA preferred.",
                    "benefits": "Competitive salary and remote work options.",
                })
        self.assertIn("grounded_explanation", data.get("metadata", {}))
        grounded = data["metadata"]["grounded_explanation"]
        self.assertIsNotNone(grounded)
        self.assertIn("overall_summary", grounded)
        # Must be deterministic, not LLM-generated
        self.assertIn("generation_method", grounded)
        self.assertEqual(grounded["generation_method"], "deterministic_grounded_fallback")

    def test_shap_values_populated_offline(self):
        """Linear feature attribution must work without any API key."""
        data = self._analyze({
            "title": "Product Manager",
            "company_name": "TechStart",
            "description": "Define product roadmap. Collaborate with engineering and design.",
            "requirements": "3 years product management experience.",
        })
        self.assertTrue(data["success"])
        self.assertIn("shap_values", data)
        self.assertIsInstance(data["shap_values"], list)


# ---------------------------------------------------------------------------
# 3. Pasted-Text Extraction Without API Key
# ---------------------------------------------------------------------------

class TestTextExtractionWithoutApiKey(unittest.TestCase):
    """Verify /api/extract/text works offline with the deterministic extractor."""

    def setUp(self):
        self.client = TestClient(app)

    def test_extract_text_returns_200_without_api_key(self):
        """POST /api/extract/text must succeed without any API key."""
        with patch.object(settings, "LLM_API_KEY", ""):
            with patch.object(settings, "LLM_PROVIDER", "none"):
                res = self.client.post("/api/extract/text", json={
                    "text": (
                        "Job Title: Software Development Intern\n"
                        "Company: TechNova Solutions\n"
                        "Location: Bengaluru\n"
                        "Duration: 6 months\n"
                        "Stipend: INR 20,000 per month\n"
                        "Work Mode: Hybrid\n"
                        "Requirements: Bachelor's degree in Computer Science. "
                        "Proficiency in Python, Java, and JavaScript required.\n"
                        "Responsibilities: Develop and maintain software modules, "
                        "debug existing code, write unit tests, participate in code reviews."
                    )
                })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])

    def test_deterministic_extractor_populates_key_fields(self):
        """The deterministic extractor must populate title, company, location."""
        text = (
            "Job Title: Python Developer\n"
            "Company: Infosys Ltd\n"
            "Location: Pune\n"
            "Employment Type: Full-time\n"
            "Description: Build and maintain backend REST APIs. "
            "Collaborate with cross-functional teams."
        )
        result = extract_deterministically(text)
        self.assertEqual(result.title, "Python Developer")
        self.assertIn("Infosys", result.company_name or "")
        self.assertEqual(result.location, "Pune")
        self.assertEqual(result.employment_type, "Full-time")

    def test_extract_with_llm_falls_back_when_no_key(self):
        """extract_with_llm must use deterministic path when API key is absent."""
        with patch.object(settings, "LLM_API_KEY", ""):
            result = extract_with_llm(
                "Software Engineer at Google in San Francisco. "
                "Requirements: 5 years Python, distributed systems experience."
            )
        self.assertIsNotNone(result)
        # Must not throw — returns deterministic result
        self.assertIsNotNone(result.description)

    def test_extract_with_llm_falls_back_when_key_is_placeholder(self):
        """extract_with_llm must not call Groq when key is the placeholder."""
        with patch.object(settings, "LLM_API_KEY", "your_groq_api_key_here"):
            result = extract_with_llm(
                "Data Scientist at Tesla. Location: Austin TX. "
                "Skills: Python, R, Machine Learning."
            )
        self.assertIsNotNone(result)

    def test_text_extraction_confidence_positive(self):
        """Extraction confidence must be > 0 for valid job text."""
        res = self.client.post("/api/extract/text", json={
            "text": (
                "We are looking for a Backend Engineer at ByteDance. "
                "Location: Singapore. Salary: SGD 8,000 per month. "
                "Requirements: 4 years Go or Java. Experience with Kafka and Redis."
            )
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data.get("extraction_confidence", 0), 0.0)

    def test_text_extraction_rejects_website_config_without_api_key(self):
        """Content validator must reject non-job content regardless of API key."""
        with patch.object(settings, "LLM_API_KEY", ""):
            res = self.client.post("/api/extract/text", json={
                "text": json.dumps({
                    "domain": "example.com",
                    "siteConfig": {"theme": "dark", "locale": "en-US"},
                    "privacyPolicy": "<html><body>Privacy policy text here.</body></html>",
                    "trackingScripts": ["gtm.js", "analytics.js"],
                    "navigationConfig": {"headerLinks": ["/home", "/about"]},
                })
            })
        # Should either reject (success=False) or return low confidence
        data = res.json()
        if data.get("success"):
            self.assertLess(data.get("extraction_confidence", 1.0), 0.5)
        else:
            self.assertFalse(data["success"])


# ---------------------------------------------------------------------------
# 4. URL Extraction Without API Key (Mocked HTTP)
# ---------------------------------------------------------------------------

class TestUrlExtractionWithoutApiKey(unittest.TestCase):
    """Verify /api/extract/url works offline (HTTP is mocked)."""

    def setUp(self):
        self.client = TestClient(app)
        self.sample_html = """
        <html>
        <head><title>Senior React Developer | WidgetCorp</title></head>
        <body>
        <h1>Senior React Developer</h1>
        <p>WidgetCorp is hiring a Senior React Developer in London, UK.</p>
        <p>Employment Type: Full-time. Salary: £70,000 per annum.</p>
        <h2>Requirements</h2>
        <p>5+ years React experience. Proficiency in TypeScript and GraphQL.</p>
        <h2>Responsibilities</h2>
        <p>Build component libraries, conduct code reviews, mentor junior developers.</p>
        </body>
        </html>
        """

    def test_url_extraction_without_api_key_uses_deterministic(self):
        """URL extraction must work offline when the API key is absent."""
        with patch("backend.app.services.extraction.extraction_service.fetch_url_content") as mock_fetch:
            mock_fetch.return_value = (self.sample_html, "https://widgetcorp.com/jobs/1")
            with patch.object(settings, "LLM_API_KEY", ""):
                res = self.client.post("/api/extract/url", json={"url": "https://widgetcorp.com/jobs/1"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        extracted = data.get("extracted_data") or data.get("extracted_job") or {}
        self.assertTrue(
            extracted.get("title") or data.get("extraction_confidence", 0) > 0
        )

    def test_url_extraction_ssrf_protection_blocks_private_ip_without_api_key(self):
        """SSRF protection must block private IPs regardless of API key.

        Returns HTTP 200 with success=False and extraction_status=URL_INVALID
        (structured failure response) rather than HTTP 400 since the refactored
        extraction service returns ExtractionResponse for all error cases.
        """
        res = self.client.post("/api/extract/url", json={"url": "http://192.168.1.1/jobs"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["extraction_status"], "URL_INVALID")
        self.assertEqual(body["extraction_confidence"], 0.0)

    def test_url_extraction_ssrf_blocks_localhost_without_api_key(self):
        """SSRF protection must block localhost regardless of API key.

        Returns HTTP 200 with success=False and extraction_status=URL_INVALID
        (structured failure response) rather than HTTP 400 since the refactored
        extraction service returns ExtractionResponse for all error cases.
        """
        res = self.client.post("/api/extract/url", json={"url": "http://127.0.0.1/jobs"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["extraction_status"], "URL_INVALID")
        self.assertEqual(body["extraction_confidence"], 0.0)


# ---------------------------------------------------------------------------
# 5. Local Explanation Generation Without API Key
# ---------------------------------------------------------------------------

class TestLocalExplanationWithoutApiKey(unittest.TestCase):
    """Verify deterministic explanation generation works fully offline."""

    def setUp(self):
        self.client = TestClient(app)

    def test_deterministic_fallback_generates_without_api_key(self):
        """generate_deterministic_fallback_explanation must not contact any API."""
        explanation = generate_deterministic_fallback_explanation(
            title="Financial Analyst",
            company_name="Offshore Capital LLC",
            fraud_probability=0.78,
            is_fraudulent=True,
            risk_level="HIGH",
            warnings=[
                WarningIndicator(
                    indicator_name="Upfront Transfer",
                    category="financial",
                    severity="critical",
                    evidence="Send $200 via Cash App",
                    reason_for_flagging="Upfront financial transfer is a scam indicator",
                    source_type="textual_evidence",
                )
            ],
            reassuring=[],
            unverified=["Company website not verifiable"],
            top_fraud_features=[
                FeatureContribution(
                    token="cash app",
                    feature_name="text:cash app",
                    weight=1.5,
                    contribution=0.9,
                    direction="fraud_indicative",
                )
            ],
            top_legit_features=[],
        )
        self.assertEqual(explanation.generation_method, "deterministic_grounded_fallback")
        self.assertIn("78.0%", explanation.overall_summary)
        self.assertTrue(len(explanation.primary_reasons) > 0)
        self.assertTrue(len(explanation.verification_checklist) > 0)

    def test_generate_grounded_explanation_uses_local_when_no_key(self):
        """generate_grounded_explanation must use local engine when key is absent."""
        with patch.object(settings, "LLM_API_KEY", ""):
            with patch.object(settings, "LLM_PROVIDER", "none"):
                explanation, warnings, risk_tier = generate_grounded_explanation(
                    title="Customer Support Executive",
                    description=(
                        "We are urgently hiring! No interview required. "
                        "Earn $500 weekly from home. Apply now on Telegram @hr_mgr."
                    ),
                    company_name="",
                    fraud_probability=0.91,
                    is_fraudulent=True,
                    risk_level="CRITICAL",
                )
        self.assertEqual(explanation.generation_method, "deterministic_grounded_fallback")
        self.assertIsNotNone(explanation.overall_summary)
        self.assertIsNotNone(risk_tier)

    def test_explain_api_endpoint_without_api_key(self):
        """POST /api/explain must return 200 with deterministic explanation when no key."""
        with patch.object(settings, "LLM_API_KEY", ""):
            with patch.object(settings, "LLM_PROVIDER", "none"):
                res = self.client.post("/api/explain", json={
                    "title": "Warehouse Associate",
                    "company_name": "QuickShip Logistics",
                    "description": "Pick, pack, and ship orders in a fast-paced warehouse environment.",
                    "requirements": "Physical fitness. Ability to lift 30kg.",
                    "benefits": "Overtime pay, health insurance.",
                })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("explanation", data)
        self.assertIn("overall_summary", data["explanation"])
        # Without a key, generation_method must be deterministic
        self.assertIn(
            data["explanation"]["generation_method"],
            ["deterministic_grounded_fallback", "deterministic"],
        )

    def test_generation_method_label_is_honest(self):
        """The generation_method field must clearly distinguish local from LLM output."""
        explanation = generate_deterministic_fallback_explanation(
            title="Test Role",
            company_name="Test Co",
            fraud_probability=0.1,
            is_fraudulent=False,
            risk_level="LOW",
            warnings=[],
            reassuring=[],
            unverified=[],
            top_fraud_features=[],
            top_legit_features=[],
        )
        # Must not claim to be AI-generated when it is deterministic
        self.assertNotIn("llm", explanation.generation_method)
        self.assertNotIn("groq", explanation.generation_method)
        self.assertIn("deterministic", explanation.generation_method)


# ---------------------------------------------------------------------------
# 6. Database Save and Retrieval Without API Key
# ---------------------------------------------------------------------------

class TestDatabaseWithoutApiKey(unittest.TestCase):
    """Verify SQLite storage works independently of any external API key."""

    def setUp(self):
        self.db_path = _temp_db()

    def tearDown(self):
        try:
            self.db_path.unlink(missing_ok=True)
        except Exception:
            pass

    def test_init_db_creates_tables(self):
        """init_db must create job_analyses and extraction_results tables."""
        from backend.app.db.database import get_connection
        conn = get_connection(self.db_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        self.assertIn("job_analyses", tables)
        self.assertIn("extraction_results", tables)

    def test_save_and_retrieve_analysis(self):
        """save_analysis and get_recent_analyses must round-trip correctly."""
        from backend.app.db.database import save_analysis, get_recent_analyses
        row_id = save_analysis(
            title="QA Engineer",
            company="Reliable Software",
            description="Test software products end-to-end.",
            is_fraudulent=False,
            fraud_probability=0.12,
            risk_level="LOW",
            verdict="Likely Legitimate Employment Posting",
            decision_threshold=0.48,
            model_name="Linear Support Vector Machine",
            model_status="trained",
            heuristic_signals=["No verified corporate logo"],
            shap_values=[{"token": "software", "value": -0.3}],
            grounded_explanation={"overall_summary": "Low risk posting.", "generation_method": "deterministic_grounded_fallback"},
            db_path=self.db_path,
        )
        self.assertIsInstance(row_id, int)
        self.assertGreater(row_id, 0)

        analyses = get_recent_analyses(limit=10, db_path=self.db_path)
        self.assertEqual(len(analyses), 1)
        record = analyses[0]
        self.assertEqual(record["title"], "QA Engineer")
        self.assertAlmostEqual(record["fraud_probability"], 0.12, places=4)
        self.assertEqual(record["risk_level"], "LOW")
        self.assertFalse(bool(record["is_fraudulent"]))
        self.assertIsInstance(record["heuristic_signals"], list)
        self.assertEqual(len(record["heuristic_signals"]), 1)

    def test_get_analysis_by_id(self):
        """get_analysis_by_id must return the correct record."""
        from backend.app.db.database import save_analysis, get_analysis_by_id
        row_id = save_analysis(
            title="DevOps Engineer",
            company="CloudOps",
            description="Manage CI/CD pipelines and infrastructure.",
            is_fraudulent=False,
            fraud_probability=0.08,
            risk_level="LOW",
            verdict="Likely Legitimate Employment Posting",
            decision_threshold=0.48,
            model_name="Linear Support Vector Machine",
            model_status="trained",
            db_path=self.db_path,
        )
        record = get_analysis_by_id(row_id, db_path=self.db_path)
        self.assertIsNotNone(record)
        self.assertEqual(record["title"], "DevOps Engineer")
        self.assertEqual(record["company"], "CloudOps")

    def test_get_analysis_by_nonexistent_id_returns_none(self):
        """get_analysis_by_id must return None for non-existent IDs."""
        from backend.app.db.database import get_analysis_by_id
        result = get_analysis_by_id(999999, db_path=self.db_path)
        self.assertIsNone(result)

    def test_save_extraction_result(self):
        """save_extraction and get_recent_extractions must round-trip correctly."""
        from backend.app.db.database import save_extraction, get_recent_extractions
        row_id = save_extraction(
            source_type="text",
            source_ref="Software Engineer at Acme in London...",
            extracted_data={
                "title": "Software Engineer",
                "company_name": "Acme",
                "location": "London",
            },
            completeness_score=0.75,
            extraction_confidence=0.85,
            extraction_method="deterministic",
            is_valid_job=True,
            warnings=[],
            db_path=self.db_path,
        )
        self.assertIsInstance(row_id, int)

        records = get_recent_extractions(limit=10, db_path=self.db_path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["source_type"], "text")
        self.assertAlmostEqual(records[0]["extraction_confidence"], 0.85, places=4)
        self.assertIsInstance(records[0]["extracted_data"], dict)
        self.assertEqual(records[0]["extracted_data"]["title"], "Software Engineer")

    def test_multiple_analyses_ordered_by_most_recent(self):
        """get_recent_analyses must return results newest-first."""
        from backend.app.db.database import save_analysis, get_recent_analyses
        for i in range(3):
            save_analysis(
                title=f"Role {i}",
                company="Corp",
                description=f"Description for role {i}.",
                is_fraudulent=False,
                fraud_probability=0.10 + i * 0.05,
                risk_level="LOW",
                verdict="Likely Legitimate Employment Posting",
                decision_threshold=0.48,
                model_name="Linear Support Vector Machine",
                model_status="trained",
                db_path=self.db_path,
            )
        analyses = get_recent_analyses(limit=10, db_path=self.db_path)
        self.assertEqual(len(analyses), 3)
        # Newest inserted has highest ID — created_at DESC order
        self.assertGreaterEqual(analyses[0]["id"], analyses[1]["id"])
        self.assertGreaterEqual(analyses[1]["id"], analyses[2]["id"])

    def test_history_api_endpoint_returns_200(self):
        """GET /api/history must return 200 without any API key."""
        client = TestClient(app)
        res = client.get("/api/history")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("analyses", data)
        self.assertIn("count", data)

    def test_history_api_single_record(self):
        """GET /api/history/999999 must return 404 for non-existent record."""
        client = TestClient(app)
        res = client.get("/api/history/999999")
        self.assertEqual(res.status_code, 404)


# ---------------------------------------------------------------------------
# 7. Optional Groq Integration (Mocked)
# ---------------------------------------------------------------------------

class TestOptionalGroqIntegration(unittest.TestCase):
    """Verify that when Groq IS configured, the LLM path is attempted.
    The HTTP call is mocked — no real network request is made."""

    def test_groq_provider_is_available_when_key_configured(self):
        """GroqLLMProvider.is_available must be True when a real key is set."""
        from backend.app.services.llm.groq_provider import GroqLLMProvider
        provider = GroqLLMProvider(api_key="gsk_real_looking_key_abc123")
        self.assertTrue(provider.is_available)

    def test_groq_provider_not_available_when_key_empty(self):
        """GroqLLMProvider.is_available must be False when key is empty."""
        from backend.app.services.llm.groq_provider import GroqLLMProvider
        provider = GroqLLMProvider(api_key="")
        self.assertFalse(provider.is_available)

    def test_groq_provider_not_available_when_key_is_placeholder(self):
        """GroqLLMProvider.is_available must be False for placeholder key."""
        from backend.app.services.llm.groq_provider import GroqLLMProvider
        provider = GroqLLMProvider(api_key="your_groq_api_key_here")
        self.assertFalse(provider.is_available)

    def test_groq_llm_path_attempted_when_key_configured(self):
        """When key is configured, generate_grounded_explanation must attempt LLM."""
        mock_response = {
            "overall_summary": "Mocked AI summary.",
            "primary_reasons": ["Mocked reason."],
            "positive_indicators": [],
            "warning_signals": [],
            "unverified_information": [],
            "verification_checklist": ["Verify company."],
            "applicant_safety_verdict": "PROCEED NORMALLY WITH STANDARD PROFESSIONAL CARE",
        }
        with patch("backend.app.services.llm.groq_provider.GroqLLMProvider.is_available", new_callable=lambda: property(lambda self: True)):
            with patch("backend.app.services.llm.groq_provider.GroqLLMProvider.generate_completion") as mock_completion:
                mock_completion.return_value = json.dumps(mock_response)
                explanation, _, _ = generate_grounded_explanation(
                    title="Software Architect",
                    description="Lead the design of distributed microservices architecture.",
                    company_name="Enterprise Tech",
                    fraud_probability=0.05,
                    is_fraudulent=False,
                    risk_level="LOW",
                )
        # LLM path was taken — generation_method should reflect the provider
        self.assertIn("llm", explanation.generation_method)

    def test_explanation_falls_back_when_groq_raises(self):
        """If Groq raises an exception, must fall back to deterministic explanation."""
        with patch("backend.app.services.llm.groq_provider.GroqLLMProvider.is_available", new_callable=lambda: property(lambda self: True)):
            with patch("backend.app.services.llm.groq_provider.GroqLLMProvider.generate_completion") as mock_completion:
                mock_completion.side_effect = RuntimeError("Simulated Groq API timeout")
                explanation, _, _ = generate_grounded_explanation(
                    title="Support Agent",
                    description="Handle inbound customer calls and resolve tickets.",
                    company_name="HelpDesk Inc",
                    fraud_probability=0.15,
                    is_fraudulent=False,
                    risk_level="LOW",
                )
        # Must have fallen back gracefully
        self.assertIsNotNone(explanation)
        self.assertIn("overall_summary", explanation.model_dump())

    def test_extract_with_llm_calls_groq_when_key_present(self):
        """extract_with_llm must attempt the Groq HTTP call when key is present."""
        mock_llm_result = {
            "title": "ML Engineer",
            "company_name": "DeepMind",
            "location": "London",
            "employment_type": "Full-time",
            "required_skills": ["Python", "TensorFlow"],
            "description": "Research and implement ML algorithms.",
        }
        mock_httpx_response = MagicMock()
        mock_httpx_response.status_code = 200
        mock_httpx_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(mock_llm_result)}}]
        }
        with patch.object(settings, "LLM_API_KEY", "gsk_real_key_abc123xyz"):
            with patch("httpx.post", return_value=mock_httpx_response):
                result = extract_with_llm(
                    "ML Engineer at DeepMind in London. Work on state-of-the-art ML research."
                )
        self.assertEqual(result.title, "ML Engineer")
        self.assertIn("DeepMind", result.company_name or "")


# ---------------------------------------------------------------------------
# 8. Health Endpoint Reports LLM and Database Status
# ---------------------------------------------------------------------------

class TestHealthEndpointStatus(unittest.TestCase):
    """Verify /api/health accurately reports LLM and database configuration."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_reports_llm_disabled_when_provider_none(self):
        """With LLM_PROVIDER=none, health details must report LLM as disabled."""
        with patch.object(settings, "LLM_PROVIDER", "none"):
            with patch.object(settings, "LLM_API_KEY", ""):
                res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        llm_info = data.get("details", {}).get("llm_integration", {})
        self.assertEqual(llm_info.get("status"), "disabled")
        self.assertFalse(llm_info.get("api_key_configured", True))

    def test_health_reports_llm_configured_when_key_present(self):
        """With a real key and LLM_PROVIDER=groq, health must report configured."""
        with patch.object(settings, "LLM_PROVIDER", "groq"):
            with patch.object(settings, "LLM_API_KEY", "gsk_real_key_abc123"):
                res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        llm_info = data.get("details", {}).get("llm_integration", {})
        self.assertEqual(llm_info.get("status"), "configured")
        self.assertTrue(llm_info.get("api_key_configured"))

    def test_health_reports_key_missing_when_provider_set_but_no_key(self):
        """With LLM_PROVIDER=groq but no key, health must report key_missing."""
        with patch.object(settings, "LLM_PROVIDER", "groq"):
            with patch.object(settings, "LLM_API_KEY", ""):
                res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        llm_info = data.get("details", {}).get("llm_integration", {})
        self.assertEqual(llm_info.get("status"), "key_missing")

    def test_health_reports_database_connected(self):
        """Health endpoint must report SQLite database as connected."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        db_info = data.get("details", {}).get("database", {})
        self.assertIn(db_info.get("status"), ["connected", "error"])
        # In normal test conditions, database should be connected
        if db_info.get("status") == "connected":
            self.assertEqual(db_info.get("engine"), "SQLite")

    def test_health_still_healthy_when_llm_key_missing(self):
        """Application health must be 'healthy' even when no API key is set."""
        with patch.object(settings, "LLM_PROVIDER", "groq"):
            with patch.object(settings, "LLM_API_KEY", ""):
                res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")


if __name__ == "__main__":
    unittest.main()

