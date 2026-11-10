"""JobShield AI — Model Feature Attribution Service.

Computes exact linear model feature attributions for incoming job postings using
the champion Calibrated Linear SVM classifier's fitted hyperplane weights.
"""

from __future__ import annotations

import logging
from typing import Any, List, Tuple
import numpy as np
from scipy import sparse
from backend.app.schemas.analysis import FeatureContribution

logger = logging.getLogger("jobshield.explainability.features")


def compute_feature_attributions(
    X_sample: sparse.csr_matrix,
    model: Any,
    feature_names: List[str],
    top_n: int = 8,
) -> Tuple[List[FeatureContribution], List[FeatureContribution], float]:
    """Calculate exact linear feature contributions (w_j * x_j) for the prediction instance."""
    try:
        # Extract weights from CalibratedClassifierCV or direct LinearSVC
        if hasattr(model, "calibrated_classifiers_"):
            weights = np.mean(
                [clf.estimator.coef_.ravel() for clf in model.calibrated_classifiers_],
                axis=0,
            )
            intercept = float(
                np.mean([clf.estimator.intercept_[0] for clf in model.calibrated_classifiers_])
            )
        elif hasattr(model, "coef_"):
            weights = model.coef_.ravel()
            intercept = float(model.intercept_[0]) if hasattr(model, "intercept_") else 0.0
        else:
            weights = np.zeros(len(feature_names))
            intercept = 0.0

        indices = X_sample.indices
        data = X_sample.data

        contributions: List[FeatureContribution] = []
        for idx, val in zip(indices, data):
            if idx < len(feature_names):
                fname = feature_names[idx]
                w = float(weights[idx])
                contrib = float(w * val)

                # Clean token display prefix
                clean_token = fname
                if fname.startswith("text:"):
                    clean_token = fname[5:]
                elif fname.startswith("cat:"):
                    clean_token = fname[4:]
                elif fname.startswith("bin:"):
                    clean_token = fname[4:]

                contributions.append(
                    FeatureContribution(
                        token=clean_token,
                        feature_name=fname,
                        weight=round(w, 4),
                        contribution=round(contrib, 4),
                        direction="fraud_indicative" if contrib > 0 else "legitimate_indicative",
                    )
                )

        fraud_indicative = sorted(
            [c for c in contributions if c.contribution > 0],
            key=lambda x: x.contribution,
            reverse=True,
        )[:top_n]

        legit_indicative = sorted(
            [c for c in contributions if c.contribution < 0],
            key=lambda x: x.contribution,
        )[:top_n]

        return fraud_indicative, legit_indicative, intercept

    except Exception as e:
        logger.error(f"Error computing linear attributions: {e}")
        return [], [], 0.0

