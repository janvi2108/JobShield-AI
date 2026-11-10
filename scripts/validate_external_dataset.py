"""JobShield AI — External Dataset Validation CLI.

Benchmarks the champion Linear SVM model against external job scam datasets
(such as the Internship Job Scam Dataset) and outputs domain generalization metrics.

Usage:
    python scripts/validate_external_dataset.py
    python scripts/validate_external_dataset.py --file data/external/internship_job_scam.csv
    python scripts/validate_external_dataset.py --output reports/external_validation_report.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.validation.evaluation import run_external_validation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("validate_external")


def main():
    parser = argparse.ArgumentParser(description="JobShield AI External Dataset Validation Tool")
    parser.add_argument("--file", type=str, default=None, help="Path to external dataset CSV file")
    parser.add_argument("--output", type=str, default=None, help="Path to save JSON comparison report")
    args = parser.parse_args()

    print("=" * 70)
    print(" JobShield AI — External Dataset Validation & Generalization Benchmark")
    print("=" * 70)

    try:
        report = run_external_validation(file_path=args.file)
    except Exception as exc:
        logger.error(f"Validation failed: {exc}", exc_info=True)
        sys.exit(1)

    internal = report.internal_benchmark
    external = report.external_benchmark
    shift = report.domain_shift

    print(f"\nModel: {report.model_name} (Threshold: {report.decision_threshold:.2f})")
    print("-" * 70)
    print(f"{'Metric':<25} | {'EMSCAD Test Split':<18} | {'External Dataset':<18} | {'Delta':<10}")
    print("-" * 70)
    print(f"{'Sample Count':<25} | {internal.sample_count:<18} | {external.sample_count:<18} | -")
    print(f"{'Fraud Prevalence':<25} | {internal.fraud_prevalence:<18.2%} | {external.fraud_prevalence:<18.2%} | -")
    print(f"{'Accuracy':<25} | {internal.accuracy:<18.4f} | {external.accuracy:<18.4f} | {external.accuracy - internal.accuracy:+.4f}")
    print(f"{'Precision (Minority)':<25} | {internal.precision:<18.4f} | {external.precision:<18.4f} | {shift.precision_delta:+.4f}")
    print(f"{'Recall (Minority)':<25} | {internal.recall:<18.4f} | {external.recall:<18.4f} | {shift.recall_delta:+.4f}")
    print(f"{'F1-Score (Minority)':<25} | {internal.f1_score:<18.4f} | {external.f1_score:<18.4f} | {external.f1_score - internal.f1_score:+.4f}")
    if internal.pr_auc is not None and external.pr_auc is not None:
        print(f"{'PR-AUC':<25} | {internal.pr_auc:<18.4f} | {external.pr_auc:<18.4f} | {external.pr_auc - internal.pr_auc:+.4f}")
    if internal.roc_auc is not None and external.roc_auc is not None:
        print(f"{'ROC-AUC':<25} | {internal.roc_auc:<18.4f} | {external.roc_auc:<18.4f} | {external.roc_auc - internal.roc_auc:+.4f}")
    print("-" * 70)

    print(f"\nGeneralization Verdict: {shift.generalization_verdict} (F1 Retention: {shift.f1_retention_percentage:.1f}%)")
    print("\nKey Observations:")
    for obs in shift.key_observations:
        print(f"  * {obs}")

    print("\nSafety & Engineering Recommendations:")
    for rec in report.recommendations:
        print(f"  - {rec}")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        print(f"\nReport saved successfully to {out_path}")

    print("=" * 70)


if __name__ == "__main__":
    main()

