"""JobShield AI — Risk Engine, HTML Sanitization, and Explanation Regression Suite.

Validates:
A. Clearly fraudulent synthetic postings (Apex Digital Careers, upfront fees, WhatsApp document extortion, guaranteed hiring).
B. Genuine legitimate postings (Microsoft Azure engineer, enterprise developer).
C. Borderline postings (company registration under Companies Act, code deposit, tuition fee reimbursement).
D. HTML-to-text extraction cleaning (no raw tags, paragraph separation, bullet preservation, entity decoding).
E. Database and history integration persistence without data loss.
"""

import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.analysis import JobAnalysisRequest
from backend.app.services.prediction_service import analyze_job_posting
from backend.app.services.extraction.text_cleaner import clean_job_text, strip_html_to_text, clean_extracted_job_fields
from backend.app.schemas.extraction import ExtractedJobData


class TestRiskEngineRegressionSuite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    # =========================================================================
    # A. CLEARLY FRAUDULENT SYNTHETIC POSTINGS
    # =========================================================================

    def test_apex_digital_careers_classified_critical(self):
        """Observed failure case: Apex Digital Careers with onboarding fee & WhatsApp Aadhaar/PAN."""
        req = JobAnalysisRequest(
            title="Junior Software Developer – Immediate Hiring",
            company_name="Apex Digital Careers Pvt. Ltd.",
            description="""
            Apex Digital Careers Pvt. Ltd. is hiring Junior Software Developers.
            Salary: INR 65,000 - 95,000 per month.
            Experience: 0-1 year. Freshers can apply.
            Urgent hiring, limited vacancies!
            Guaranteed job confirmation within 24 hours. No technical interview or coding assessment required.
            Refundable onboarding fee of INR 3,499 required for training and account setup.
            Submit your Aadhaar and PAN documents through WhatsApp at +91 9876543210 for immediate processing.
            """,
            requirements="0-1 year experience, Bachelor degree, freshers welcome.",
            benefits="High salary, immediate joining.",
        )
        res = analyze_job_posting(req)

        # Verdict must be fraudulent and risk level must be CRITICAL
        self.assertTrue(res.is_fraudulent)
        self.assertEqual(res.verdict, "Potentially Fraudulent Job Posting")
        self.assertEqual(res.risk_level, "CRITICAL")
        self.assertGreaterEqual(res.score, 0.75)

        # Raw ML probability must remain preserved in metadata
        self.assertIn("ml_fraud_probability", res.metadata)

        # Grounded explanation must reflect critical warning signals and safety recommendation
        grounded = res.metadata.get("grounded_explanation")
        self.assertIsNotNone(grounded)
        self.assertIn("DO NOT APPLY", grounded["applicant_safety_verdict"])
        self.assertIn("CRITICAL", grounded["overall_summary"])

        # Warnings must flag onboarding fee and WhatsApp identity document extortion
        flagged_indicators = [w["indicator_name"] for w in grounded.get("warning_signals", [])]
        self.assertTrue(
            any("Fee" in name or "Deposit" in name for name in flagged_indicators)
        )
        self.assertTrue(
            any("Identity" in name or "WhatsApp" in name for name in flagged_indicators)
        )

    def test_advance_registration_fee_scam(self):
        """Upfront registration fee demand must trigger fraud classification."""
        req = JobAnalysisRequest(
            title="Remote Data Entry Clerk",
            company_name="Quick Hire Global",
            description="""
            Earn $4,000/month working from home! No experience required.
            Immediate placement. You must pay a mandatory $199 registration fee for verification software.
            Payment accepted via wire transfer or cryptocurrency.
            """,
        )
        res = analyze_job_posting(req)
        self.assertTrue(res.is_fraudulent)
        self.assertIn(res.risk_level, ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(res.score, 0.48)

    # =========================================================================
    # B. LEGITIMATE POSTINGS
    # =========================================================================

    def test_microsoft_posting_remains_low_risk(self):
        """Genuine Microsoft careers posting must remain classified as LOW risk."""
        req = JobAnalysisRequest(
            title="Software Engineer II",
            company_name="Microsoft Corporation",
            description="""
            At Microsoft, we are looking for a Software Engineer II to develop scalable cloud infrastructure on Azure.
            Responsibilities:
            • Design and implement microservices in C#, Go, and Python.
            • Participate in Agile sprints, code reviews, and architectural reviews.
            • Collaborate with cross-functional teams to improve reliability and performance.
            Requirements:
            • Bachelor degree in Computer Science, Engineering, or related technical field.
            • 3+ years of professional software engineering experience.
            • Experience with cloud computing, distributed systems, and CI/CD pipelines.
            Benefits include comprehensive healthcare coverage, 401(k) matching, parental leave, and wellness stipends.
            Apply directly on our official career portal: careers.microsoft.com.
            """,
            requirements="Bachelor degree in Computer Science, 3+ years experience with distributed systems.",
            benefits="Health insurance, 401(k), parental leave.",
            has_company_logo=True,
            has_questions=True,
        )
        res = analyze_job_posting(req)
        self.assertFalse(res.is_fraudulent)
        self.assertEqual(res.verdict, "Likely Legitimate Employment Posting")
        self.assertEqual(res.risk_level, "LOW")
        self.assertLess(res.score, 0.25)

        # Explanation must NOT contain junk tokens or claims of verifying organizational legitimacy
        grounded = res.metadata.get("grounded_explanation")
        self.assertIsNotNone(grounded)
        self.assertEqual(grounded["applicant_safety_verdict"], "PROCEED NORMALLY WITH STANDARD PROFESSIONAL CARE")

        for reason in grounded.get("primary_reasons", []):
            self.assertNotIn("verified organizational legitimacy", reason)
            self.assertNotIn("'11'", reason)
            self.assertNotIn("'list'", reason)

    # =========================================================================
    # C. BORDERLINE POSTINGS (CONTEXTUAL AWARENESS)
    # =========================================================================

    def test_contextual_registration_not_flagged(self):
        """Legitimate company registration or repository code deposit must not trigger false positive."""
        req = JobAnalysisRequest(
            title="Senior Backend Architect",
            company_name="Global Fintech Solutions",
            description="""
            Global Fintech Solutions is registered under the Companies Act and compliant with banking regulations.
            We require engineers to deposit code into our private GitHub repositories daily.
            Our company covers all examination fees and tuition fees for continuing education.
            Candidates will participate in technical interviews and system design assessments.
            Official correspondence: careers@globalfintech.com.
            """,
            has_company_logo=True,
        )
        res = analyze_job_posting(req)
        self.assertFalse(res.is_fraudulent)
        self.assertIn(res.risk_level, ["LOW", "MODERATE"])

        # No critical upfront fee warning should be flagged
        grounded = res.metadata.get("grounded_explanation")
        if grounded:
            crit_warnings = [w for w in grounded.get("warning_signals", []) if w.get("severity") == "critical"]
            self.assertEqual(len(crit_warnings), 0)

    # =========================================================================
    # D. HTML EXTRACTION AND SANITIZATION
    # =========================================================================

    def test_strip_html_converts_tags_to_structured_text(self):
        """Verify HTML paragraphs and lists are properly transformed without raw tags."""
        raw_html = "<p>Responsibilities</b><br><ul><li>Develop software applications</li><li>Run unit tests</li></ul>"
        cleaned = clean_job_text(raw_html)

        # Must not contain any HTML tags
        self.assertNotIn("<p>", cleaned)
        self.assertNotIn("</p>", cleaned)
        self.assertNotIn("<ul>", cleaned)
        self.assertNotIn("</ul>", cleaned)
        self.assertNotIn("<li>", cleaned)
        self.assertNotIn("</li>", cleaned)
        self.assertNotIn("<br>", cleaned)
        self.assertNotIn("</b>", cleaned)

        # Must contain readable text with bullet point
        self.assertIn("Responsibilities", cleaned)
        self.assertIn("• Develop software applications", cleaned)
        self.assertIn("• Run unit tests", cleaned)

    def test_clean_extracted_job_fields_cleans_all_fields(self):
        """Verify every field in ExtractedJobData is cleaned of raw HTML tags and entities."""
        job = ExtractedJobData(
            title="<h1>Lead Developer</h1>",
            company_name="<strong>InnovateX &amp; Co.</strong>",
            description="<p>Full job description</p><ul><li>Responsibility 1</li></ul>",
            requirements="<p>Requirements:</p><ul><li>Bachelor's &amp; Master's degree</li></ul>",
            responsibilities="<p>Daily tasks:</p><ul><li>Code reviews</li></ul>",
            compensation="<strong>$120,000 &ndash; $140,000</strong> per year",
            benefits="<ul><li>Health &amp; dental insurance</li></ul>",
        )
        clean_extracted_job_fields(job)

        for field_name in ["title", "company_name", "description", "requirements", "responsibilities", "compensation", "benefits"]:
            val = getattr(job, field_name)
            self.assertIsNotNone(val)
            self.assertNotIn("<", val)
            self.assertNotIn(">", val)
            self.assertNotIn("&amp;", val)
            self.assertNotIn("&ndash;", val)

    # =========================================================================
    # E. INTEGRATION & PERSISTENCE
    # =========================================================================

    def test_api_analyze_persists_to_db_and_returns_consistent_verdict(self):
        """End-to-end API test: analyze endpoint persists and returns synchronized verdict."""
        payload = {
            "title": "Junior Python Developer",
            "company_name": "Verified Cloud Corp",
            "description": "Standard Python backend developer position. Experience with FastAPI and PostgreSQL. Apply at careers@verifiedcloud.com.",
            "requirements": "Bachelor degree in Computer Science or related field.",
            "benefits": "Medical, dental, and 401(k) matching.",
            "has_company_logo": True,
        }
        res = self.client.post("/api/analyze", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("metadata", data)
        self.assertIn("analysis_id", data["metadata"])
        self.assertIsNotNone(data["metadata"]["analysis_id"])

        # Verdict and risk level agreement
        if data["is_fraudulent"]:
            self.assertEqual(data["verdict"], "Potentially Fraudulent Job Posting")
            self.assertIn(data["risk_level"], ["HIGH", "CRITICAL"])
        else:
            self.assertEqual(data["verdict"], "Likely Legitimate Employment Posting")
            self.assertIn(data["risk_level"], ["LOW", "MODERATE"])


if __name__ == "__main__":
    unittest.main()

