"""JobShield AI — SQLAlchemy ORM & Multi-Table Tests.

Validates:
  1. Database initialization and table creation (5 core tables + extraction table)
  2. Multi-table atomic persistence across JobAnalysis, FraudPrediction, ExtractedDetails, EvidenceFindings, AIExplanation
  3. Cascading foreign-key deletion
  4. Search, filtering, and pagination logic on /api/analyses
  5. Live statistics aggregation without fabrication
  6. REST API routes: GET /analyses, GET /analyses/stats, GET /analyses/{id}, DELETE /analyses/{id}
  7. Prediction API enriches response with analysis_id and persistence_status
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import (
    init_db,
    save_analysis,
    get_analysis_by_id,
    get_analyses_list,
    delete_analysis,
    get_analysis_stats,
    get_session,
)
from backend.app.db.models import (
    JobAnalysis,
    FraudPrediction,
    ExtractedDetails,
    EvidenceFinding,
    AIExplanation,
)


class TestDatabaseORMSuite(unittest.TestCase):
    def setUp(self):
        self.tmp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_file.close()
        self.db_path = Path(self.tmp_file.name)
        init_db(self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        try:
            self.db_path.unlink(missing_ok=True)
        except Exception:
            pass

    def test_init_db_creates_all_tables(self):
        """Verify that all core tables exist in the schema."""
        from backend.app.db.database import get_connection
        conn = get_connection(self.db_path)
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        conn.close()
        expected = {
            "job_analyses",
            "fraud_predictions",
            "extracted_details",
            "evidence_findings",
            "ai_explanations",
            "extraction_results",
        }
        for exp in expected:
            self.assertIn(exp, tables)

    def test_save_analysis_creates_related_records(self):
        """Verify that save_analysis atomically populates all 5 relational models."""
        analysis_id = save_analysis(
            title="Senior Full-Stack Engineer",
            company="TechNova Solutions",
            description="Build scalable distributed web applications using React and FastAPI.",
            is_fraudulent=False,
            fraud_probability=0.08,
            risk_level="LOW",
            verdict="Likely Legitimate Employment Posting",
            decision_threshold=0.48,
            model_name="Linear Support Vector Machine",
            model_status="trained",
            heuristic_signals=["Free webmail address used for official hiring inquiries"],
            shap_values=[{"token": "react", "value": -0.4}],
            grounded_explanation={
                "overall_summary": "Legitimate enterprise posting with strong technical requirements.",
                "primary_reasons": ["Verified organizational terminology"],
                "verification_checklist": ["Confirm domain name"],
                "applicant_safety_verdict": "PROCEED NORMALLY",
                "generation_method": "deterministic_grounded_fallback",
            },
            requirements="5+ years Python, TypeScript",
            benefits="Health, 401k",
            employment_type="Full-time",
            db_path=self.db_path,
        )
        self.assertIsInstance(analysis_id, int)
        self.assertGreater(analysis_id, 0)

        # Inspect database using ORM session
        with get_session(self.db_path) as session:
            analysis = session.get(JobAnalysis, analysis_id)
            self.assertIsNotNone(analysis)
            self.assertEqual(analysis.title, "Senior Full-Stack Engineer")
            self.assertIsNotNone(analysis.prediction)
            self.assertFalse(analysis.prediction.is_fraudulent)
            self.assertEqual(analysis.prediction.risk_level, "LOW")
            self.assertIsNotNone(analysis.extracted_details)
            self.assertEqual(analysis.extracted_details.employment_type, "Full-time")
            self.assertEqual(len(analysis.evidence_findings), 1)
            self.assertEqual(analysis.evidence_findings[0].category, "communication")
            self.assertIsNotNone(analysis.explanation)
            self.assertEqual(analysis.explanation.generation_method, "deterministic_grounded_fallback")

    def test_cascading_deletion(self):
        """Deleting a JobAnalysis must remove child predictions, findings, and explanations."""
        analysis_id = save_analysis(
            title="Target Deletion Role",
            company="Bad Actors Inc",
            description="Pay $100 fee for equipment.",
            is_fraudulent=True,
            fraud_probability=0.92,
            risk_level="CRITICAL",
            verdict="Potentially Fraudulent Job Posting",
            decision_threshold=0.48,
            model_name="Linear Support Vector Machine",
            model_status="trained",
            heuristic_signals=["Financial solicitation or upfront registration/training fee requested"],
            grounded_explanation={"overall_summary": "Scam detected"},
            db_path=self.db_path,
        )

        with get_session(self.db_path) as session:
            # Confirm rows exist
            pred_count = session.query(FraudPrediction).filter_by(analysis_id=analysis_id).count()
            self.assertEqual(pred_count, 1)

        # Delete through helper
        deleted = delete_analysis(analysis_id, db_path=self.db_path)
        self.assertTrue(deleted)

        # Confirm all children are cascaded
        with get_session(self.db_path) as session:
            self.assertIsNone(session.get(JobAnalysis, analysis_id))
            self.assertEqual(session.query(FraudPrediction).filter_by(analysis_id=analysis_id).count(), 0)
            self.assertEqual(session.query(ExtractedDetails).filter_by(analysis_id=analysis_id).count(), 0)
            self.assertEqual(session.query(EvidenceFinding).filter_by(analysis_id=analysis_id).count(), 0)
            self.assertEqual(session.query(AIExplanation).filter_by(analysis_id=analysis_id).count(), 0)

    def test_get_analysis_by_id_full_tree(self):
        """get_analysis_by_id returns composite dictionary with all sub-entities."""
        analysis_id = save_analysis(
            title="Data Scientist",
            company="Deep Analytics",
            description="Train ML pipelines and evaluate feature attributions.",
            is_fraudulent=False,
            fraud_probability=0.15,
            risk_level="LOW",
            verdict="Legitimate",
            decision_threshold=0.48,
            model_name="Linear SVM",
            model_status="trained",
            heuristic_signals=[],
            db_path=self.db_path,
        )
        record = get_analysis_by_id(analysis_id, db_path=self.db_path)
        self.assertIsNotNone(record)
        self.assertEqual(record["id"], analysis_id)
        self.assertEqual(record["title"], "Data Scientist")
        self.assertEqual(record["fraud_probability"], 0.15)
        self.assertIn("extracted_details", record)
        self.assertIn("evidence_findings", record)

    def test_pagination_and_filtering(self):
        """Test get_analyses_list pagination and search."""
        for i in range(5):
            save_analysis(
                title=f"Engineer {i}",
                company="Corp Alpha" if i % 2 == 0 else "Beta LLC",
                description="Test description",
                is_fraudulent=(i % 2 == 1),
                fraud_probability=0.85 if (i % 2 == 1) else 0.10,
                risk_level="HIGH" if (i % 2 == 1) else "LOW",
                verdict="Evaluated",
                decision_threshold=0.48,
                model_name="Linear SVM",
                model_status="trained",
                db_path=self.db_path,
            )

        # Page 1 with page_size=2
        items, total, pages = get_analyses_list(page=1, page_size=2, db_path=self.db_path)
        self.assertEqual(len(items), 2)
        self.assertEqual(total, 5)
        self.assertEqual(pages, 3)

        # Filter by fraudulent
        fraud_items, fraud_total, _ = get_analyses_list(
            page=1, page_size=10, classification="fraudulent", db_path=self.db_path
        )
        self.assertEqual(fraud_total, 2)
        for it in fraud_items:
            self.assertTrue(it["is_fraudulent"])

        # Search by company
        alpha_items, alpha_total, _ = get_analyses_list(
            page=1, page_size=10, search_company="Alpha", db_path=self.db_path
        )
        self.assertEqual(alpha_total, 3)

    def test_live_statistics_computation(self):
        """Verify get_analysis_stats computes live stats without fabrication."""
        stats_empty = get_analysis_stats(db_path=self.db_path)
        self.assertEqual(stats_empty["total_analyses"], 0)
        self.assertEqual(stats_empty["fraudulent_count"], 0)
        self.assertEqual(stats_empty["legitimate_count"], 0)
        self.assertEqual(stats_empty["fraud_percentage"], 0.0)

        # Insert 1 fraud and 1 legit
        save_analysis(
            title="Scam 1",
            company="Fake Co",
            description="Deposit fee",
            is_fraudulent=True,
            fraud_probability=0.90,
            risk_level="CRITICAL",
            verdict="Fraud",
            decision_threshold=0.48,
            model_name="SVM",
            model_status="trained",
            db_path=self.db_path,
        )
        save_analysis(
            title="Legit 1",
            company="Real Co",
            description="Good job",
            is_fraudulent=False,
            fraud_probability=0.05,
            risk_level="LOW",
            verdict="Legit",
            decision_threshold=0.48,
            model_name="SVM",
            model_status="trained",
            db_path=self.db_path,
        )

        stats = get_analysis_stats(db_path=self.db_path)
        self.assertEqual(stats["total_analyses"], 2)
        self.assertEqual(stats["fraudulent_count"], 1)
        self.assertEqual(stats["legitimate_count"], 1)
        self.assertEqual(stats["high_risk_count"], 1)
        self.assertEqual(stats["fraud_percentage"], 50.0)

    # -----------------------------------------------------------------------
    # API Route Integration Tests
    # -----------------------------------------------------------------------

    def test_api_analyses_list_endpoint(self):
        """GET /api/analyses returns 200 with paginated payload."""
        res = self.client.get("/api/analyses?page=1&page_size=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("analyses", data)
        self.assertIn("pagination", data)

    def test_api_analyses_stats_endpoint(self):
        """GET /api/analyses/stats returns 200 with required aggregation keys."""
        res = self.client.get("/api/analyses/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("total_analyses", data)
        self.assertIn("fraudulent_count", data)
        self.assertIn("legitimate_count", data)
        self.assertIn("high_risk_count", data)
        self.assertIn("today_count", data)

    def test_api_analyses_delete_flow(self):
        """DELETE /api/analyses/{id} removes record; subsequent GET returns 404."""
        # Create record via direct POST /api/analyze
        post_res = self.client.post(
            "/api/analyze",
            json={
                "title": "Temporary Role for Deletion API Test",
                "company_name": "Ephemeral Inc",
                "description": "Standard software engineer responsibilities with tests and code reviews.",
            },
        )
        self.assertEqual(post_res.status_code, 200)
        ana_id = post_res.json().get("metadata", {}).get("analysis_id")
        self.assertIsNotNone(ana_id)

        # GET detail returns 200
        get_res = self.client.get(f"/api/analyses/{ana_id}")
        self.assertEqual(get_res.status_code, 200)

        # DELETE returns 200
        del_res = self.client.delete(f"/api/analyses/{ana_id}")
        self.assertEqual(del_res.status_code, 200)

        # Subsequent GET returns 404
        get_after = self.client.get(f"/api/analyses/{ana_id}")
        self.assertEqual(get_after.status_code, 404)

    def test_api_analyze_enriches_response_with_analysis_id(self):
        """POST /api/analyze must include 'analysis_id' and 'persistence_status' in metadata."""
        post_res = self.client.post(
            "/api/analyze",
            json={
                "title": "Backend Python Architect",
                "company_name": "JobShield Systems",
                "description": "Design high-throughput fraud detection engine using FastAPI and scikit-learn.",
            },
        )
        self.assertEqual(post_res.status_code, 200)
        meta = post_res.json().get("metadata", {})
        self.assertIn("analysis_id", meta)
        self.assertIsNotNone(meta["analysis_id"])
        self.assertEqual(meta["persistence_status"], "saved")


if __name__ == "__main__":
    unittest.main()

