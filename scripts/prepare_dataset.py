"""JobShield AI — EMSCAD Dataset Preparation & Partitioning Tool.

Prepares the raw EMSCAD dataset for ML modeling by:
1. Validating and mapping the 'fraudulent' target column to binary {0, 1}.
2. Excluding the data-leakage metadata column 'in_balanced_dataset'.
3. Deduplicating exact duplicate rows to prevent cross-partition leakage.
4. Generating reproducible, stratified Train (80%), Validation (10%), and Test (10%) splits.
5. Saving processed CSV partitions and structured split metadata.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

try:
    from .inspect_dataset import inspect_dataset, read_csv_with_fallback, resolve_dataset_path
except (ImportError, ValueError):
    from inspect_dataset import inspect_dataset, read_csv_with_fallback, resolve_dataset_path


RANDOM_SEED_DEFAULT = 42
TRAIN_RATIO_DEFAULT = 0.80
VAL_RATIO_DEFAULT = 0.10
TEST_RATIO_DEFAULT = 0.10

TARGET_COLUMN = "fraudulent"
LEAKAGE_COLUMNS = ["in_balanced_dataset"]


def validate_and_map_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Validate and map 'fraudulent' column to standard integer binary {0, 1}.

    Supported raw encodings:
      - 'f'/'t' (Aegean EMSCAD original)
      - '0'/'1' or 0/1
      - 'false'/'true' (case-insensitive)

    Raises ValueError if target column is missing, contains nulls, or has unexpected values.
    """
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' is missing from the dataset.")

    target_series = df[TARGET_COLUMN]

    # Check for null targets
    null_count = int(target_series.isnull().sum())
    if null_count > 0:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' contains {null_count} null/missing values. "
            "Supervised learning requires valid ground-truth labels for all records."
        )

    # Standardize values for mapping
    # Create normalized representation
    normalized = target_series.copy()
    if normalized.dtype == object or isinstance(normalized.iloc[0], str):
        normalized = normalized.astype(str).str.strip().str.lower()

    unique_vals = set(normalized.unique())

    # Supported mappings to binary (0 = Legitimate, 1 = Fraudulent)
    valid_mappings = {
        # 'f'/'t' mapping
        "f": 0,
        "t": 1,
        # string '0'/'1'
        "0": 0,
        "1": 1,
        # integer 0/1 (when converted to str)
        0: 0,
        1: 1,
        # 'false'/'true'
        "false": 0,
        "true": 1,
    }

    # Verify that every unique value can be mapped
    unmapped = unique_vals - set(valid_mappings.keys())
    if unmapped:
        raise ValueError(
            f"Unexpected labels encountered in '{TARGET_COLUMN}': {unmapped}. "
            f"Expected binary labels matching one of: {list(valid_mappings.keys())}."
        )

    # Apply mapping
    mapped_target = normalized.map(valid_mappings).astype(int)

    df_out = df.copy()
    df_out[TARGET_COLUMN] = mapped_target

    target_info = {
        "original_unique_labels": [str(x) for x in target_series.unique().tolist()],
        "mapped_unique_labels": [0, 1],
        "legitimate_count_0": int((mapped_target == 0).sum()),
        "fraudulent_count_1": int((mapped_target == 1).sum()),
        "fraud_prevalence_pct": round(float((mapped_target == 1).mean() * 100), 2),
    }

    return df_out, target_info


def deduplicate_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Remove exact duplicate rows across all features to prevent cross-partition leakage."""
    initial_rows = len(df)
    exact_duplicates = int(df.duplicated().sum())

    if exact_duplicates > 0:
        cleaned_df = df.drop_duplicates(keep="first").reset_index(drop=True)
    else:
        cleaned_df = df.reset_index(drop=True)

    dedup_info = {
        "initial_rows": initial_rows,
        "exact_duplicates_removed": exact_duplicates,
        "retained_rows": len(cleaned_df),
        "deduplication_policy": (
            "Exact duplicate records across all columns were removed (keeping first occurrence) "
            "to prevent identical job advertisements from spanning across train and test partitions."
        ),
    }

    return cleaned_df, dedup_info


def remove_leakage_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Exclude known metadata columns that introduce ground-truth or sampling leakage."""
    dropped_cols = []
    df_out = df.copy()

    for col in LEAKAGE_COLUMNS:
        if col in df_out.columns:
            df_out = df_out.drop(columns=[col])
            dropped_cols.append(col)

    return df_out, dropped_cols


def create_stratified_splits(
    df: pd.DataFrame,
    random_seed: int = RANDOM_SEED_DEFAULT,
    train_ratio: float = TRAIN_RATIO_DEFAULT,
    val_ratio: float = VAL_RATIO_DEFAULT,
    test_ratio: float = TEST_RATIO_DEFAULT,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Create reproducible, stratified 80:10:10 train, validation, and test splits."""
    total_ratio = train_ratio + val_ratio + test_ratio
    if not np.isclose(total_ratio, 1.0):
        raise ValueError(
            f"Split ratios must sum to 1.0. Got: {train_ratio} + {val_ratio} + {test_ratio} = {total_ratio}"
        )

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' required for stratified split.")

    # Step 1: Stratified split into train (train_ratio) and temp (val_ratio + test_ratio)
    temp_ratio = val_ratio + test_ratio
    train_df, temp_df = train_test_split(
        df,
        test_size=temp_ratio,
        random_state=random_seed,
        stratify=df[TARGET_COLUMN],
        shuffle=True,
    )

    # Step 2: Stratified split of temp into validation and test (e.g. 50/50 of temp when val=0.1, test=0.1)
    relative_test_ratio = test_ratio / temp_ratio
    val_df, test_df = train_test_split(
        temp_df,
        test_size=relative_test_ratio,
        random_state=random_seed,
        stratify=temp_df[TARGET_COLUMN],
        shuffle=True,
    )

    # Disjointness & integrity verification
    train_indices = set(train_df.index)
    val_indices = set(val_df.index)
    test_indices = set(test_df.index)

    overlap_train_val = len(train_indices & val_indices)
    overlap_train_test = len(train_indices & test_indices)
    overlap_val_test = len(val_indices & test_indices)

    if overlap_train_val > 0 or overlap_train_test > 0 or overlap_val_test > 0:
        raise RuntimeError(
            f"Integrity check failed: partitions are not disjoint! "
            f"Overlaps - train/val: {overlap_train_val}, train/test: {overlap_train_test}, val/test: {overlap_val_test}"
        )

    total_split_rows = len(train_df) + len(val_df) + len(test_df)
    if total_split_rows != len(df):
        raise RuntimeError(
            f"Integrity check failed: total split rows ({total_split_rows}) != input rows ({len(df)})"
        )

    def compute_partition_stats(part_df: pd.DataFrame, name: str) -> Dict[str, Any]:
        count_0 = int((part_df[TARGET_COLUMN] == 0).sum())
        count_1 = int((part_df[TARGET_COLUMN] == 1).sum())
        total = len(part_df)
        pct_1 = round((count_1 / total * 100), 2) if total > 0 else 0.0
        return {
            "partition": name,
            "total_samples": total,
            "percentage_of_dataset": round(total / len(df) * 100, 2),
            "legitimate_count_0": count_0,
            "fraudulent_count_1": count_1,
            "fraud_prevalence_pct": pct_1,
        }

    splits_summary = {
        "random_seed": random_seed,
        "intended_ratios": {
            "train": train_ratio,
            "validation": val_ratio,
            "test": test_ratio,
        },
        "partitions_disjoint": True,
        "partitions": {
            "train": compute_partition_stats(train_df, "train"),
            "validation": compute_partition_stats(val_df, "validation"),
            "test": compute_partition_stats(test_df, "test"),
        },
    }

    return train_df, val_df, test_df, splits_summary


def prepare_emscad_dataset(
    data_path: Path | str,
    output_dir: Path | str = "data/processed",
    random_seed: int = RANDOM_SEED_DEFAULT,
    train_ratio: float = TRAIN_RATIO_DEFAULT,
    val_ratio: float = VAL_RATIO_DEFAULT,
    test_ratio: float = TEST_RATIO_DEFAULT,
) -> Dict[str, Any]:
    """Execute complete dataset preparation, validation, and stratified splitting pipeline."""
    resolved_path = Path(data_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Source dataset not found: {resolved_path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Inspect raw dataset and generate inspection report
    inspection_report_path = out_dir / "dataset_report.json"
    inspection_report = inspect_dataset(resolved_path, output_json_path=inspection_report_path)

    # 2. Read dataset
    df, encoding = read_csv_with_fallback(resolved_path)

    # 3. Target verification & binary mapping
    df_mapped, target_info = validate_and_map_target(df)

    # 4. Leakage columns exclusion
    df_no_leakage, dropped_leakage_cols = remove_leakage_columns(df_mapped)

    # 5. Deduplication
    cleaned_df, dedup_info = deduplicate_dataframe(df_no_leakage)

    # 6. Stratified Partitioning (80:10:10)
    train_df, val_df, test_df, splits_summary = create_stratified_splits(
        cleaned_df,
        random_seed=random_seed,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
    )

    # 7. Save processed partitions
    train_path = out_dir / "train.csv"
    val_path = out_dir / "validation.csv"
    test_path = out_dir / "test.csv"

    train_df.to_csv(train_path, index=False, encoding="utf-8")
    val_df.to_csv(val_path, index=False, encoding="utf-8")
    test_df.to_csv(test_path, index=False, encoding="utf-8")

    # 8. Save comprehensive split summary
    full_summary: Dict[str, Any] = {
        "source_dataset_path": str(resolved_path),
        "source_dataset_rows": len(df),
        "source_dataset_cols": df.shape[1],
        "detected_encoding": encoding,
        "target_column": TARGET_COLUMN,
        "target_mapping_info": target_info,
        "excluded_leakage_columns": dropped_leakage_cols,
        "deduplication_summary": dedup_info,
        "split_configuration": splits_summary,
        "output_artifacts": {
            "train_csv": str(train_path),
            "validation_csv": str(val_path),
            "test_csv": str(test_path),
            "dataset_report_json": str(inspection_report_path),
        },
    }

    summary_json_path = out_dir / "split_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(full_summary, f, indent=2)

    return full_summary


def print_preparation_summary(summary: Dict[str, Any]) -> None:
    """Print readable execution summary to console."""
    print("=" * 70)
    print("  JobShield AI — EMSCAD Dataset Preparation Complete")
    print("=" * 70)
    print(f"Source File:         {summary['source_dataset_path']}")
    print(f"Original Records:    {summary['source_dataset_rows']:,}")
    print(f"Deduplicated Rows:   {summary['deduplication_summary']['exact_duplicates_removed']:,}")
    print(f"Retained Records:    {summary['deduplication_summary']['retained_rows']:,}")
    print(f"Excluded Leakage:    {summary['excluded_leakage_columns']}")
    print("-" * 70)

    print("Target Distribution (After Mapping {0: Legitimate, 1: Fraudulent}):")
    tinfo = summary["target_mapping_info"]
    print(f"  Class 0 (Legitimate): {tinfo['legitimate_count_0']:,}")
    print(f"  Class 1 (Fraudulent): {tinfo['fraudulent_count_1']:,} ({tinfo['fraud_prevalence_pct']}%)")
    print("-" * 70)

    print("Stratified Partitions (Seed: 42, Target Ratios: 80 / 10 / 10):")
    for name, stats in summary["split_configuration"]["partitions"].items():
        print(
            f"  - {name.capitalize():11s}: {stats['total_samples']:,} samples ({stats['percentage_of_dataset']}%) "
            f"| Fraud: {stats['fraudulent_count_1']:,} ({stats['fraud_prevalence_pct']}%) "
            f"| Legitimate: {stats['legitimate_count_0']:,}"
        )
    print("-" * 70)

    print("Generated Artifacts in data/processed/:")
    for k, v in summary["output_artifacts"].items():
        print(f"  - {k:22s} -> {v}")
    print("=" * 70)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare EMSCAD dataset and create stratified train/val/test splits."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to the raw EMSCAD CSV file (defaults to search in data/raw/).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save train.csv, validation.csv, test.csv, and summaries.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=RANDOM_SEED_DEFAULT,
        help="Random seed for reproducible stratified splitting (default: 42).",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=TRAIN_RATIO_DEFAULT,
        help="Proportion of data for training split (default: 0.80).",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=VAL_RATIO_DEFAULT,
        help="Proportion of data for validation split (default: 0.10).",
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=TEST_RATIO_DEFAULT,
        help="Proportion of data for test split (default: 0.10).",
    )

    args = parser.parse_args()

    try:
        resolved = resolve_dataset_path(args.data_path)
    except FileNotFoundError as e:
        print(f"\n[ERROR] Dataset not found: {e}", file=sys.stderr)
        return 1

    try:
        summary = prepare_emscad_dataset(
            data_path=resolved,
            output_dir=args.output_dir,
            random_seed=args.random_seed,
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
            test_ratio=args.test_ratio,
        )
        print_preparation_summary(summary)
        return 0
    except Exception as exc:
        print(f"\n[ERROR] Dataset preparation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
