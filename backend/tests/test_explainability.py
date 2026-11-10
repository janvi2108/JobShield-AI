"""JobShield AI — Explainability & Evidence Unit and Integration Tests.

Validates deterministic evidence extraction, feature attributions, composite risk tiers,
grounded AI explanation generation, and /api/explain endpoint behavior.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.explanation import GroundedAIExplanation, WarningIndicator
from backend.app.services.explainability.evidence_generator import extract_evidence_findings
from backend.app.services.explainability.risk_analyzer import analyze_composite_risk
from backend.app.services.llm.explanation_service import (
    generate_deterministic_fallback_explanation,
    generate_grounded_explanation,
)
from backend.app.schemas.analysis import FeatureContribution


class TestExplainabilitySuite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_evidence_findings_detection(self):
        """Verify deterministic scanner flags upfront fees, telegram, and webmail."""
        title = "Urgent Remote Data Entry Representative"
        description = (
            "Immediate hire guaranteed! Please pay a refundable $150 registration fee for your onboarding kit. "
            "Send money via wire transfer or Cash App. Contact manager on Telegram @hr_lead or recruiter@gmail.com. "
            "Apply within 24 hours, limited spots left!"
        )
        warnings, reassuring, unverified = extract_evidence_findings(
            title=title,
            description=description,
            company_name="",
        )

        categories = {w.category for w in warnings}
        self.assertIn("financial", categories)
        self.assertIn("communication", categories)
        self.assertTrue(any(w.severity == "critical" for w in warnings))
        self.assertTrue(any("company" in u.lower() for u in unverified))

    def test_evidence_findings_reassuring_signals(self):
        """Verify scanner identifies positive organizational legitimacy indicators."""
        title = "Senior Software Engineer"
        description = (
            "We offer competitive salary, health insurance, 401(k) matching, and paid parental leave. "
            "Inquiries can be directed to careers@enterprise.com. Background checks and standard technical "
            "interviews are conducted."
        )
        warnings, reassuring, unverified = extract_evidence_findings(
            title=title,
            description=description,
            company_name="Enterprise Systems Inc",
            company_profile="Founded in 2010 with 500+ employees globally.",
        )

        names = {r.indicator_name for r in reassuring}
        self.assertTrue(
            "Corporate Domain Email" in names
            or "Comprehensive Compensation & Benefits" in names
            or "Structured Professional Requirements" in names
        )

    def test_composite_risk_analysis(self):
        """Verify tiered risk classification based on ML probability and evidence."""
        # Critical warning triggers CRITICAL tier
        crit_warning = [
            WarningIndicator(
                indicator_name="Upfront Fee",
                category="financial",
                severity="critical",
                evidence="$200 registration fee",
                reason_for_flagging="Scam signature",
                source_type="textual_evidence",
            )
        ]
        tier, _ = analyze_composite_risk(fraud_probability=0.30, decision_threshold=0.48, warning_indicators=crit_warning)
        self.assertEqual(tier, "CRITICAL")

        # High probability triggers HIGH tier
        tier_high, _ = analyze_composite_risk(fraud_probability=0.60, decision_threshold=0.48, warning_indicators=[])
        self.assertEqual(tier_high, "HIGH")

        # Moderate probability triggers MODERATE tier
        tier_mod, _ = analyze_composite_risk(fraud_probability=0.30, decision_threshold=0.48, warning_indicators=[])
        self.assertEqual(tier_mod, "MODERATE")

        # Low probability triggers LOW tier
        tier_low, _ = analyze_composite_risk(fraud_probability=0.04, decision_threshold=0.48, warning_indicators=[])
        self.assertEqual(tier_low, "LOW")

    def test_deterministic_fallback_explanation(self):
        """Verify rich structured explanation is generated without an external LLM."""
        explanation = generate_deterministic_fallback_explanation(
            title="Executive Assistant",
            company_name="Global Trade Ltd",
            fraud_probability=0.82,
            is_fraudulent=True,
            risk_level="CRITICAL",
            warnings=[
                WarningIndicator(
                    indicator_name="Fee Required",
                    category="financial",
                    severity="critical",
                    evidence="pay $50",
                    reason_for_flagging="Fee demand",
                    source_type="textual_evidence",
                )
            ],
            reassuring=[],
            unverified=["Missing company website"],
            top_fraud_features=[
                FeatureContribution(
                    token="moneygram",
                    feature_name="text:moneygram",
                    weight=1.2,
                    contribution=0.8,
                    direction="fraud_indicative",
                )
            ],
            top_legit_features=[],
        )

        self.assertIsInstance(explanation, GroundedAIExplanation)
        self.assertEqual(explanation.generation_method, "deterministic_grounded_fallback")
        self.assertTrue(len(explanation.primary_reasons) > 0)
        self.assertTrue(len(explanation.verification_checklist) > 0)
        self.assertIn("CRITICAL", explanation.overall_summary)

    def test_explain_api_endpoint(self):
        """Verify POST /api/explain returns 200 with structured response."""
        payload = {
            "title": "Data Analyst Intern",
            "company_name": "Apex Analytics",
            "description": "Join our analytics team to build dashboards and SQL queries. Required degree in STEM.",
            "requirements": "Proficiency in SQL, Python, and Tableau.",
            "benefits": "Competitive stipend and mentorship.",
        }
        res = self.client.post("/api/explain", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("explanation", data)
        self.assertIn("overall_summary", data["explanation"])
        self.assertIn("applicant_safety_verdict", data["explanation"])
        self.assertIn("risk_level", data)

    def test_analyze_api_enriches_with_grounded_explanation(self):
        """Verify POST /api/analyze includes grounded explanation in metadata."""
        payload = {
            "title": "Customer Service Representative",
            "company_name": "TestCorp",
            "description": "Assist customers with inbound inquiries. Full time position with benefits.",
            "requirements": "High school diploma and communication skills.",
            "benefits": "Medical, dental, vision insurance.",
        }
        res = self.client.post("/api/analyze", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("grounded_explanation", data.get("metadata", {}))
        self.assertIsNotNone(data["metadata"]["grounded_explanation"])


if __name__ == "__main__":
    unittest.main()
