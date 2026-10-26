"""JobShield AI ? ML Preprocessor and Pipeline Definitions.

Defines the reusable feature extractor and preprocessor used for both
model training and live production inference.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder

TARGET_COL = "fraudulent"
TEXT_COLS = ["title", "company_profile", "description", "requirements", "benefits"]
BINARY_COLS = ["telecommuting", "has_company_logo", "has_questions"]
CAT_COLS = ["employment_type", "required_experience", "required_education"]


def extract_combined_text(df: pd.DataFrame) -> pd.Series:
    """Combine textual attributes into a single unified document per record."""
    parts = []
    for col in TEXT_COLS:
        if col in df.columns:
            s = df[col].fillna("").astype(str).str.strip()
        else:
            s = pd.Series("", index=df.index, dtype=str)
        parts.append(s)

    combined = parts[0]
    for s in parts[1:]:
        combined = combined + " " + s
    return combined


def extract_binary_features(df: pd.DataFrame) -> np.ndarray:
    """Extract binary indicator features normalizing 't'/1/True to 1.0, else 0.0."""
    features = []
    for col in BINARY_COLS:
        if col in df.columns:
            vals = df[col].astype(str).str.strip().str.lower()
            binary_val = vals.isin(["t", "true", "1", "1.0"]).astype(float).values
        else:
            binary_val = np.zeros(len(df), dtype=float)
        features.append(binary_val.reshape(-1, 1))
    return np.hstack(features)


class EMSCADPreprocessor:
    """Reusable preprocessing and feature extraction pipeline for training and inference."""

    def __init__(
        self,
        max_features: int = 10000,
        ngram_range: Tuple[int, int] = (1, 2),
    ) -> None:
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            sublinear_tf=True,
            min_df=2,
            stop_words="english",
        )
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=True)
        self.feature_names: List[str] = []

    def fit(self, train_df: pd.DataFrame) -> EMSCADPreprocessor:
        """Fit transformations strictly on training data."""
        # 1. Text TF-IDF
        texts = extract_combined_text(train_df)
        self.vectorizer.fit(texts)
        text_features = [f"text:{w}" for w in self.vectorizer.get_feature_names_out()]

        # 2. Categoricals One-Hot
        cat_df = train_df[CAT_COLS].fillna("missing").astype(str)
        self.encoder.fit(cat_df)
        cat_features = [f"cat:{c}" for c in self.encoder.get_feature_names_out()]

        # 3. Binary columns
        bin_features = [f"bin:{c}" for c in BINARY_COLS]

        self.feature_names = text_features + cat_features + bin_features
        return self

    def transform(self, df: pd.DataFrame) -> sparse.csr_matrix:
        """Transform input dataframe into sparse feature matrix."""
        texts = extract_combined_text(df)
        X_text = self.vectorizer.transform(texts)

        cat_df = df[CAT_COLS].fillna("missing").astype(str) if all(c in df.columns for c in CAT_COLS) else pd.DataFrame("missing", index=df.index, columns=CAT_COLS)
        X_cat = self.encoder.transform(cat_df)

        X_bin = sparse.csr_matrix(extract_binary_features(df))

        X_all = sparse.hstack([X_text, X_cat, X_bin], format="csr")
        return X_all

    def fit_transform(self, train_df: pd.DataFrame) -> sparse.csr_matrix:
        return self.fit(train_df).transform(train_df)
