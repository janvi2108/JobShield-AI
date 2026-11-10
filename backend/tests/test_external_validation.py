"""JobShield AI — External Dataset Validation Tests.

Validates schema adaptation, metric calculations, domain shift analysis, and /api/validation/external endpoint.
"""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.validation import ValidationComparisonResponse
from backend.app.services.validation.evaluation import run_external_validation
from backend.app.services.validation.external_dataset import (
    create_internship_benchmark_samples,
    load_and_adapt_external_dataset,
)


class TestExternalValidationSuite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_benchmark_dataset_generation(self):
        """Verify the synthesized benchmark dataset contains required schema columns."""
        df = create_internship_benchmark_samples()
        self.assertGreater(len(df), 20)
        self.assertIn("fraudulent", df.columns)
        self.assertIn("title", df.columns)
        self.assertIn("description", df.columns)
        self.assertEqual(set(df["fraudulent"].unique()), {0, 1})

    def test_load_and_adapt_external_dataset(self):
        """Verify loader returns clean DataFrame with normalized columns."""
        df, source_name = load_and_adapt_external_dataset()
        self.assertIsNotNone(df)
        self.assertTrue(len(df) > 0)
        self.assertIn("Synthetic", source_name)

    def test_run_external_validation_pipeline(self):
        """Verify end-to-end evaluation pipeline computes metrics and domain shift."""
        report = run_external_validation()
        self.assertIsInstance(report, ValidationComparisonResponse)
        self.assertTrue(report.success)
        self.assertGreater(report.internal_benchmark.sample_count, 1000)
        self.assertGreater(report.external_benchmark.sample_count, 10)
        self.assertGreater(report.domain_shift.f1_retention_percentage, 0.0)
        self.assertIn(
            report.domain_shift.generalization_verdict,
            ["EXCELLENT", "ROBUST", "MODERATE_DEGRADATION", "SIGNIFICANT_SHIFT"],
        )

    def test_validation_api_endpoint(self):
        """Verify GET /api/validation/external returns 200 with complete comparison payload."""
        res = self.client.get("/api/validation/external")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("internal_benchmark", data)
        self.assertIn("external_benchmark", data)
        self.assertIn("domain_shift", data)
        self.assertIn("f1_retention_percentage", data["domain_shift"])


if __name__ == "__main__":
    unittest.main()

