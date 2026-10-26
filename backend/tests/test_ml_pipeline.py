import numpy as np
import pandas as pd
import pytest
from scipy import sparse
from backend.app.services.ml_pipeline import (
    EMSCADPreprocessor,
    extract_combined_text,
    extract_binary_features,
    TEXT_COLS,
    BINARY_COLS,
    CAT_COLS,
)


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        "title": ["Software Engineer", "Urgent Data Entry Wire Transfer", "Marketing Intern"],
        "company_profile": ["Tech startup building SaaS", "Anonymous offshore group", "Global media agency"],
        "description": ["Build Python and TypeScript services with senior mentors.", "Earn guaranteed $800/week no experience wire transfer required.", "Create digital marketing campaigns."],
        "requirements": ["BS in Computer Science or equivalent", "No degree required, computer with internet", "Enrolled in marketing degree"],
        "benefits": ["Competitive pay and healthcare", "Instant cash payout", "Academic credit"],
        "telecommuting": ["f", "t", "f"],
        "has_company_logo": ["t", "f", "t"],
        "has_questions": ["t", "f", "t"],
        "employment_type": ["Full-time", "Contract", "Internship"],
        "required_experience": ["Mid-Senior level", "Entry level", "Internship"],
        "required_education": ["Bachelor's Degree", "Unspecified", "Associate Degree"],
    })


def test_extract_combined_text(sample_dataframe):
    texts = extract_combined_text(sample_dataframe)
    assert len(texts) == 3
    assert "Software Engineer" in texts.iloc[0]
    assert "Urgent Data Entry" in texts.iloc[1]
    assert "Marketing Intern" in texts.iloc[2]


def test_extract_binary_features(sample_dataframe):
    bin_features = extract_binary_features(sample_dataframe)
    assert bin_features.shape == (3, 3)
    # telecommuting: ['f', 't', 'f'] -> [0, 1, 0]
    assert bin_features[0, 0] == 0.0
    assert bin_features[1, 0] == 1.0
    assert bin_features[2, 0] == 0.0

    # has_company_logo: ['t', 'f', 't'] -> [1, 0, 1]
    assert bin_features[0, 1] == 1.0
    assert bin_features[1, 1] == 0.0
    assert bin_features[2, 1] == 1.0


def test_preprocessor_fit_transform(sample_dataframe):
    prep = EMSCADPreprocessor(max_features=100, ngram_range=(1, 2))
    X = prep.fit_transform(sample_dataframe)

    assert sparse.issparse(X)
    assert X.shape[0] == 3
    assert len(prep.feature_names) > 0

    # Ensure transforming new data produces matching feature dimension
    test_sample = sample_dataframe.iloc[:1].copy()
    X_test = prep.transform(test_sample)
    assert X_test.shape == (1, X.shape[1])
