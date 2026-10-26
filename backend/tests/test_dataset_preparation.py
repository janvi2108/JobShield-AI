"""Automated unit tests for EMSCAD dataset inspection and preparation pipeline.

Uses small, explicitly synthetic fixtures to verify data preparation logic,
target mapping, leakage prevention, deduplication, and stratified split integrity.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from scripts.inspect_dataset import (
    inspect_dataset,
    resolve_dataset_path,
)
from scripts.prepare_dataset import (
    TARGET_COLUMN,
    create_stratified_splits,
    deduplicate_dataframe,
    prepare_emscad_dataset,
    remove_leakage_columns,
    validate_and_map_target,
)


@pytest.fixture
def synthetic_raw_dataframe():
    """Create a minimal synthetic fixture mimicking EMSCAD schema for unit testing only."""
    np.random.seed(42)
    n_samples = 100

    titles = [f"Job Title {i}" for i in range(n_samples)]
    descriptions = [f"This is description for job {i}" for i in range(n_samples)]
    companies = [f"Company {i % 20}" for i in range(n_samples)]

    # 10% fraudulent labels as 'f' and 't' (matching raw EMSCAD format)
    labels = ["t" if i < 10 else "f" for i in range(n_samples)]

    # Metadata column to be tested for leakage exclusion
    in_balanced = [1 if i % 2 == 0 else 0 for i in range(n_samples)]

    df = pd.DataFrame(
        {
            "title": titles,
            "company_profile": companies,
            "description": descriptions,
            "requirements": ["Requirements text" for _ in range(n_samples)],
            "benefits": ["Benefits text" for _ in range(n_samples)],
            "telecommuting": [0 for _ in range(n_samples)],
            "has_company_logo": [1 for _ in range(n_samples)],
            "has_questions": [0 for _ in range(n_samples)],
            "employment_type": ["Full-time" for _ in range(n_samples)],
            "required_experience": ["Entry level" for _ in range(n_samples)],
            "required_education": ["Bachelor's" for _ in range(n_samples)],
            "industry": ["Technology" for _ in range(n_samples)],
            "function": ["Engineering" for _ in range(n_samples)],
            "in_balanced_dataset": in_balanced,
            "fraudulent": labels,
        }
    )

    # Inject 4 exact duplicate rows to test deduplication
    duplicates = df.iloc[:4].copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    return df


def test_validate_and_map_target_valid_ft():
    """Verify 'f'/'t' targets are cleanly converted to binary {0, 1}."""
    df = pd.DataFrame({"fraudulent": ["f", "t", "f", "f", "t"]})
    mapped_df, info = validate_and_map_target(df)

    assert mapped_df["fraudulent"].tolist() == [0, 1, 0, 0, 1]
    assert info["legitimate_count_0"] == 3
    assert info["fraudulent_count_1"] == 2
    assert info["mapped_unique_labels"] == [0, 1]


def test_validate_and_map_target_valid_strings_0_1():
    """Verify '0'/'1' and 0/1 target formats are supported."""
    df = pd.DataFrame({"fraudulent": ["0", "1", "0", 1, 0]})
    mapped_df, _ = validate_and_map_target(df)
    assert mapped_df["fraudulent"].tolist() == [0, 1, 0, 1, 0]


def test_validate_and_map_target_unexpected_labels():
    """Verify ValueError is raised if unexpected labels exist."""
    df = pd.DataFrame({"fraudulent": ["f", "t", "scam_posting", "f"]})
    with pytest.raises(ValueError, match="Unexpected labels encountered"):
        validate_and_map_target(df)


def test_validate_and_map_target_null_values():
    """Verify ValueError is raised if target contains nulls."""
    df = pd.DataFrame({"fraudulent": ["f", None, "t", "f"]})
    with pytest.raises(ValueError, match="contains 1 null/missing values"):
        validate_and_map_target(df)


def test_validate_and_map_target_missing_column():
    """Verify ValueError is raised if target column does not exist."""
    df = pd.DataFrame({"some_other_column": [1, 2, 3]})
    with pytest.raises(ValueError, match="missing from the dataset"):
        validate_and_map_target(df)


def test_deduplicate_dataframe():
    """Verify exact duplicate rows are removed and counted accurately."""
    df = pd.DataFrame({"a": [1, 1, 2, 3], "b": ["x", "x", "y", "z"]})
    cleaned_df, dedup_info = deduplicate_dataframe(df)

    assert len(cleaned_df) == 3
    assert dedup_info["exact_duplicates_removed"] == 1
    assert dedup_info["retained_rows"] == 3


def test_remove_leakage_columns():
    """Verify metadata column 'in_balanced_dataset' is excluded from output."""
    df = pd.DataFrame(
        {
            "title": ["Job A", "Job B"],
            "in_balanced_dataset": [1, 0],
            "fraudulent": [0, 1],
        }
    )
    cleaned_df, dropped = remove_leakage_columns(df)

    assert "in_balanced_dataset" not in cleaned_df.columns
    assert "in_balanced_dataset" in dropped
    assert "title" in cleaned_df.columns
    assert "fraudulent" in cleaned_df.columns


def test_create_stratified_splits_integrity_and_disjointness():
    """Verify 80:10:10 stratified partitioning produces mutually disjoint subsets."""
    # 100 records: 10 fraud (10%), 90 legitimate (90%)
    labels = [1] * 10 + [0] * 90
    df = pd.DataFrame({"id": list(range(100)), "fraudulent": labels})

    train_df, val_df, test_df, summary = create_stratified_splits(
        df,
        random_seed=42,
        train_ratio=0.80,
        val_ratio=0.10,
        test_ratio=0.10,
    )

    # 1. Size checks
    assert len(train_df) == 80
    assert len(val_df) == 10
    assert len(test_df) == 10
    assert len(train_df) + len(val_df) + len(test_df) == 100

    # 2. Disjointness check
    train_idx = set(train_df.index)
    val_idx = set(val_df.index)
    test_idx = set(test_df.index)

    assert len(train_idx & val_idx) == 0
    assert len(train_idx & test_idx) == 0
    assert len(val_idx & test_idx) == 0
    assert summary["partitions_disjoint"] is True

    # 3. Stratification check: 10% fraud ratio should be preserved across partitions
    assert train_df["fraudulent"].sum() == 8   # 8 / 80 = 10%
    assert val_df["fraudulent"].sum() == 1     # 1 / 10 = 10%
    assert test_df["fraudulent"].sum() == 1    # 1 / 10 = 10%


def test_create_stratified_splits_reproducibility():
    """Verify that using the fixed random seed produces strictly deterministic partitions."""
    labels = [1] * 10 + [0] * 90
    df = pd.DataFrame({"id": list(range(100)), "fraudulent": labels})

    train_1, val_1, test_1, _ = create_stratified_splits(df, random_seed=42)
    train_2, val_2, test_2, _ = create_stratified_splits(df, random_seed=42)

    assert train_1.index.tolist() == train_2.index.tolist()
    assert val_1.index.tolist() == val_2.index.tolist()
    assert test_1.index.tolist() == test_2.index.tolist()


def test_prepare_emscad_dataset_end_to_end_on_fixture(tmp_path, synthetic_raw_dataframe):
    """Verify full preparation workflow on a synthetic fixture in an isolated temp directory."""
    raw_csv = tmp_path / "raw_synthetic_emscad.csv"
    processed_dir = tmp_path / "processed"

    synthetic_raw_dataframe.to_csv(raw_csv, index=False, encoding="utf-8")

    summary = prepare_emscad_dataset(
        data_path=raw_csv,
        output_dir=processed_dir,
        random_seed=42,
    )

    # Verify generated files
    assert (processed_dir / "train.csv").exists()
    assert (processed_dir / "validation.csv").exists()
    assert (processed_dir / "test.csv").exists()
    assert (processed_dir / "dataset_report.json").exists()
    assert (processed_dir / "split_summary.json").exists()

    # Verify deduplication was applied (4 duplicate rows removed from 104 -> 100)
    assert summary["source_dataset_rows"] == 104
    assert summary["deduplication_summary"]["exact_duplicates_removed"] == 4
    assert summary["deduplication_summary"]["retained_rows"] == 100

    # Verify leakage exclusion
    train_loaded = pd.read_csv(processed_dir / "train.csv")
    assert "in_balanced_dataset" not in train_loaded.columns
    assert set(train_loaded["fraudulent"].unique()).issubset({0, 1})


def test_resolve_dataset_path_missing():
    """Verify FileNotFoundError is raised when dataset is missing."""
    with pytest.raises(FileNotFoundError, match="Specified dataset path does not exist"):
        resolve_dataset_path("non_existent_folder/missing_file.csv")


def test_deduplicate_dataframe_tracks_target_distribution():
    """Verify deduplication tracks fraud vs legitimate duplicate counts accurately."""
    df = pd.DataFrame({
        "title": ["Job A", "Job A", "Job B", "Job C", "Job C"],
        "description": ["Desc A", "Desc A", "Desc B", "Desc C", "Desc C"],
        "fraudulent": [1, 1, 0, 0, 0],
    })
    cleaned, info = deduplicate_dataframe(df)
    assert len(cleaned) == 3
    assert info["exact_duplicates_removed"] == 2
    assert info["duplicates_fraudulent_1"] == 1
    assert info["duplicates_legitimate_0"] == 1
    assert info["retained_fraudulent_1"] == 1
    assert info["retained_legitimate_0"] == 2


def test_processed_emscad_files_integrity():
    """Verify actual generated processed files exist and match exact verified row counts."""
    processed_dir = Path("data/processed")
    if not (processed_dir / "train.csv").exists():
        pytest.skip("Processed EMSCAD files not yet generated.")

    train_df = pd.read_csv(processed_dir / "train.csv")
    val_df = pd.read_csv(processed_dir / "validation.csv")
    test_df = pd.read_csv(processed_dir / "test.csv")

    assert len(train_df) == 14105
    assert len(val_df) == 1763
    assert len(test_df) == 1764

    # Verify target distributions
    assert int((train_df["fraudulent"] == 1).sum()) == 685
    assert int((train_df["fraudulent"] == 0).sum()) == 13420

    assert int((val_df["fraudulent"] == 1).sum()) == 85
    assert int((val_df["fraudulent"] == 0).sum()) == 1678

    assert int((test_df["fraudulent"] == 1).sum()) == 86
    assert int((test_df["fraudulent"] == 0).sum()) == 1678

    # Sum of fraudulent across splits
    total_fraud = (train_df["fraudulent"] == 1).sum() + (val_df["fraudulent"] == 1).sum() + (test_df["fraudulent"] == 1).sum()
    assert total_fraud == 856

    # Verify leakage column excluded
    for df in [train_df, val_df, test_df]:
        assert "in_balanced_dataset" not in df.columns
        assert "fraudulent" in df.columns
