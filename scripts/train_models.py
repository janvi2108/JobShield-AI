"""JobShield AI ? Machine Learning Model Training & Benchmark Evaluation.

Trains, evaluates, and compares 4 candidate classifiers on the prepared EMSCAD splits:
1. Logistic Regression
2. Linear Support Vector Machine (Calibrated)
3. Random Forest Classifier
4. XGBoost Classifier

Evaluates candidates on the validation split using PR-AUC and F1-score (minority class).
Tunes the optimal decision threshold for the winning classifier on validation data.
Computes final unbiased performance metrics on the untouched test split.
Persists the champion model pipeline to models/model.joblib and benchmark metrics to models/metrics.json.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC
import xgboost as xgb


RANDOM_SEED = 42
import sys
sys.path.insert(0, ".")
from backend.app.services.ml_pipeline import (
    EMSCADPreprocessor,
    extract_combined_text,
    extract_binary_features,
    TEXT_COLS,
    BINARY_COLS,
    CAT_COLS,
    TARGET_COL,
)


def tune_decision_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> Tuple[float, float]:
    """Find decision threshold that maximizes minority class F1-score on validation data."""
    thresholds = np.linspace(0.10, 0.85, 76)
    best_thresh = 0.50
    best_f1 = 0.0

    for thresh in thresholds:
        preds = (y_prob >= thresh).astype(int)
        score = f1_score(y_true, preds, pos_label=1, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_thresh = float(thresh)

    return round(best_thresh, 3), round(best_f1, 4)


def evaluate_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float,
) -> Dict[str, Any]:
    """Compute comprehensive evaluation metrics at a specified decision threshold."""
    y_pred = (y_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()

    pr_auc = average_precision_score(y_true, y_prob)
    roc_auc = roc_auc_score(y_true, y_prob)
    f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
    precision = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    recall = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    accuracy = accuracy_score(y_true, y_pred)

    return {
        "threshold": threshold,
        "pr_auc": round(float(pr_auc), 4),
        "roc_auc": round(float(roc_auc), 4),
        "f1_minority": round(float(f1), 4),
        "precision_minority": round(float(precision), 4),
        "recall_minority": round(float(recall), 4),
        "accuracy": round(float(accuracy), 4),
        "confusion_matrix": {
            "true_negative": int(cm[0][0]),
            "false_positive": int(cm[0][1]),
            "false_negative": int(cm[1][0]),
            "true_positive": int(cm[1][1]),
        },
    }


def train_and_evaluate_models(
    train_path: str = "data/processed/train.csv",
    val_path: str = "data/processed/validation.csv",
    test_path: str = "data/processed/test.csv",
    output_model_dir: str = "models",
) -> Dict[str, Any]:
    """Execute full model training, threshold tuning, candidate selection, and test evaluation."""
    print("=" * 70)
    print("  JobShield AI ? ML Training & Candidate Evaluation Pipeline")
    print("=" * 70)

    # 1. Load data splits
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    y_train = train_df[TARGET_COL].values
    y_val = val_df[TARGET_COL].values
    y_test = test_df[TARGET_COL].values

    print(f"Loaded partitions:")
    print(f"  - Train:      {len(train_df):,} samples ({int((y_train == 1).sum()):,} fraudulent, {int((y_train == 0).sum()):,} legitimate)")
    print(f"  - Validation: {len(val_df):,} samples ({int((y_val == 1).sum()):,} fraudulent, {int((y_val == 0).sum()):,} legitimate)")
    print(f"  - Test:       {len(test_df):,} samples ({int((y_test == 1).sum()):,} fraudulent, {int((y_test == 0).sum()):,} legitimate)")

    # Class imbalance ratio in training set
    neg_count = int((y_train == 0).sum())
    pos_count = int((y_train == 1).sum())
    scale_pos_weight = round(neg_count / pos_count, 2)
    print(f"Training Class Imbalance: 1:{scale_pos_weight:.1f} (Minority fraud ratio: {pos_count / len(y_train) * 100:.2f}%)")
    print("-" * 70)

    # 2. Fit Preprocessor strictly on training data
    print("Fitting feature extraction pipeline on training data...")
    preprocessor = EMSCADPreprocessor(max_features=10000, ngram_range=(1, 2))
    X_train = preprocessor.fit_transform(train_df)
    X_val = preprocessor.transform(val_df)
    X_test = preprocessor.transform(test_df)
    print(f"Extracted feature matrix shape: {X_train.shape} ({len(preprocessor.feature_names):,} total features)")
    print("-" * 70)

    # 3. Configure Candidate Classifiers
    candidates = {
        "Logistic Regression": LogisticRegression(
            C=1.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_SEED,
        ),
        "Linear Support Vector Machine": CalibratedClassifierCV(
            LinearSVC(
                C=1.0,
                class_weight="balanced",
                random_state=RANDOM_SEED,
            ),
            method="sigmoid",
            cv=3,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=16,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
    }

    results = {}
    fitted_models = {}

    for name, model in candidates.items():
        print(f"Training candidate: {name}...")
        start_time = datetime.datetime.now()
        model.fit(X_train, y_train)
        elapsed = (datetime.datetime.now() - start_time).total_seconds()

        # Predict probability on validation split
        val_probs = model.predict_proba(X_val)[:, 1]

        # Tune threshold on validation split
        best_thresh, _ = tune_decision_threshold(y_val, val_probs)

        # Compute validation metrics
        val_metrics = evaluate_predictions(y_val, val_probs, best_thresh)
        val_metrics["training_time_seconds"] = round(elapsed, 2)
        val_metrics["default_threshold_metrics"] = evaluate_predictions(y_val, val_probs, 0.50)

        results[name] = val_metrics
        fitted_models[name] = model

        print(f"  ? {name:30s} | Val PR-AUC: {val_metrics['pr_auc']:.4f} | Val F1: {val_metrics['f1_minority']:.4f} "
              f"| Prec: {val_metrics['precision_minority']:.4f} | Recall: {val_metrics['recall_minority']:.4f} "
              f"| Thresh: {best_thresh:.3f} ({elapsed:.1f}s)")

    print("-" * 70)

    # 4. Model Selection based on Validation PR-AUC and F1-score
    # Sort candidates by PR-AUC primarily, then F1-score
    sorted_candidates = sorted(
        results.items(),
        key=lambda item: (item[1]["pr_auc"], item[1]["f1_minority"]),
        reverse=True,
    )
    champion_name, champion_val_metrics = sorted_candidates[0]
    champion_model = fitted_models[champion_name]
    champion_threshold = champion_val_metrics["threshold"]

    print(f"SELECTED CHAMPION MODEL: {champion_name}")
    print(f"Selection Basis: Highest Validation PR-AUC ({champion_val_metrics['pr_auc']:.4f}) and Minority F1-score ({champion_val_metrics['f1_minority']:.4f})")
    print(f"Optimal Decision Threshold: {champion_threshold}")
    print("-" * 70)

    # 5. Final Unbiased Evaluation on Held-Out Test Split
    print("Evaluating Champion Model on Untouched Test Split...")
    test_probs = champion_model.predict_proba(X_test)[:, 1]
    test_metrics = evaluate_predictions(y_test, test_probs, champion_threshold)

    print(f"Final Test Split Results ({champion_name} @ threshold={champion_threshold}):")
    print(f"  - Test PR-AUC:      {test_metrics['pr_auc']:.4f}")
    print(f"  - Test ROC-AUC:     {test_metrics['roc_auc']:.4f}")
    print(f"  - Test F1-Score:    {test_metrics['f1_minority']:.4f}")
    print(f"  - Test Precision:   {test_metrics['precision_minority']:.4f}")
    print(f"  - Test Recall:      {test_metrics['recall_minority']:.4f}")
    print(f"  - Test Accuracy:    {test_metrics['accuracy']:.4f}")
    cm = test_metrics["confusion_matrix"]
    print(f"  - Confusion Matrix: TN={cm['true_negative']}, FP={cm['false_positive']}, FN={cm['false_negative']}, TP={cm['true_positive']}")
    print("=" * 70)

    # 6. Persist Model and Metadata
    out_dir = Path(output_model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    artifact_bundle = {
        "model_name": champion_name,
        "model": champion_model,
        "preprocessor": preprocessor,
        "decision_threshold": champion_threshold,
        "feature_names": preprocessor.feature_names,
        "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "training_metadata": {
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
            "fraud_prevalence_pct": round(pos_count / len(y_train) * 100, 2),
            "random_seed": RANDOM_SEED,
        },
    }

    model_path = out_dir / "model.joblib"
    joblib.dump(artifact_bundle, model_path, compress=3)
    print(f"Saved champion pipeline artifact -> {model_path}")

    # Build comprehensive metrics output
    metrics_summary = {
        "project": "JobShield AI",
        "benchmark_dataset": "Aegean University EMSCAD (Embarrassingly Shallow Model Comparison)",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "selected_model": {
            "name": champion_name,
            "decision_threshold": champion_threshold,
            "selection_rationale": "Highest validation PR-AUC and minority class F1-score across 4 candidates.",
        },
        "candidate_comparison": results,
        "test_evaluation": {
            "model_name": champion_name,
            "metrics": test_metrics,
        },
        "dataset_splits": {
            "train": {"total": len(train_df), "fraudulent": pos_count, "legitimate": neg_count},
            "validation": {"total": len(val_df), "fraudulent": int((y_val == 1).sum()), "legitimate": int((y_val == 0).sum())},
            "test": {"total": len(test_df), "fraudulent": int((y_test == 1).sum()), "legitimate": int((y_test == 0).sum())},
        },
    }

    metrics_path = out_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"Saved benchmark telemetry JSON -> {metrics_path}")
    print("=" * 70)

    return metrics_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and evaluate JobShield AI candidate classifiers.")
    parser.add_argument("--train-path", default="data/processed/train.csv")
    parser.add_argument("--val-path", default="data/processed/validation.csv")
    parser.add_argument("--test-path", default="data/processed/test.csv")
    parser.add_argument("--output-dir", default="models")

    args = parser.parse_args()
    try:
        train_and_evaluate_models(
            train_path=args.train_path,
            val_path=args.val_path,
            test_path=args.test_path,
            output_model_dir=args.output_dir,
        )
        return 0
    except Exception as e:
        print(f"[ERROR] Training failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
