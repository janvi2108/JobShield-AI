"""JobShield AI — EMSCAD Dataset Inspection Tool.

Performs thorough structural, statistical, and data-quality inspection
of the raw Employment Scam Aegean Dataset (EMSCAD).
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


DEFAULT_SEARCH_PATHS = [
    Path("data/raw/DataSet.csv"),
    Path("data/raw/emscad_dataset.csv"),
    Path("data/raw/emscad.csv"),
    Path("data/raw/dataset.csv"),
]

TEXT_COLUMNS_OF_INTEREST = [
    "title",
    "company_profile",
    "description",
    "requirements",
    "benefits",
]


def resolve_dataset_path(custom_path: Optional[str] = None) -> Path:
    """Resolve the dataset file path from custom argument or default candidates.

    Raises FileNotFoundError if no candidate exists.
    """
    if custom_path:
        p = Path(custom_path)
        if p.exists() and p.is_file():
            return p
        raise FileNotFoundError(f"Specified dataset path does not exist: {custom_path}")

    for candidate in DEFAULT_SEARCH_PATHS:
        if candidate.exists() and candidate.is_file():
            return candidate

    search_dirs = [str(p) for p in DEFAULT_SEARCH_PATHS]
    raise FileNotFoundError(
        f"EMSCAD dataset CSV not found. Checked default locations:\n  "
        + "\n  ".join(search_dirs)
        + "\n\nPlease supply the file path via --data-path or place 'DataSet.csv' in data/raw/."
    )


def read_csv_with_fallback(file_path: Path) -> Tuple[pd.DataFrame, str]:
    """Read CSV file with automatic fallback across common encodings."""
    encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    last_error: Optional[Exception] = None

    for enc in encodings_to_try:
        try:
            df = pd.read_csv(file_path, encoding=enc, low_memory=False)
            return df, enc
        except (UnicodeDecodeError, pd.errors.ParserError) as err:
            last_error = err
            continue

    raise RuntimeError(
        f"Unable to read CSV at {file_path} using encodings {encodings_to_try}. Last error: {last_error}"
    )


def compute_text_statistics(series: pd.Series) -> Dict[str, Any]:
    """Calculate character and word count distribution for a text column."""
    valid_text = series.dropna().astype(str)
    if len(valid_text) == 0:
        return {
            "non_null_count": 0,
            "char_length": None,
            "word_length": None,
        }

    char_lens = valid_text.str.len()
    word_lens = valid_text.str.split().str.len()

    return {
        "non_null_count": int(len(valid_text)),
        "char_length": {
            "min": int(char_lens.min()),
            "median": float(char_lens.median()),
            "mean": float(round(char_lens.mean(), 2)),
            "max": int(char_lens.max()),
        },
        "word_length": {
            "min": int(word_lens.min()),
            "median": float(word_lens.median()),
            "mean": float(round(word_lens.mean(), 2)),
            "max": int(word_lens.max()),
        },
    }


def inspect_dataset(
    file_path: Path | str,
    output_json_path: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """Run full inspection on an EMSCAD CSV file and return structured report."""
    resolved_path = Path(file_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {resolved_path}")

    file_size_bytes = resolved_path.stat().st_size
    file_size_mb = round(file_size_bytes / (1024 * 1024), 3)

    df, detected_encoding = read_csv_with_fallback(resolved_path)
    total_rows, total_cols = df.shape

    # 1. Missing value counts & percentages
    missing_counts = df.isnull().sum()
    missing_pcts = (missing_counts / total_rows * 100).round(2)
    missing_summary = {
        col: {
            "missing_count": int(missing_counts[col]),
            "missing_percentage": float(missing_pcts[col]),
        }
        for col in df.columns
    }

    # 2. Duplicate analysis
    exact_duplicates_count = int(df.duplicated().sum())
    exact_duplicates_pct = round(exact_duplicates_count / total_rows * 100, 2)

    # Check textual subset duplicates (if text columns present)
    text_cols_present = [c for c in ["title", "description", "company_profile"] if c in df.columns]
    text_duplicates_count = int(df.duplicated(subset=text_cols_present).sum()) if text_cols_present else 0

    # 3. Target label distribution
    target_summary: Dict[str, Any] = {}
    if "fraudulent" in df.columns:
        target_series = df["fraudulent"]
        raw_unique_values = [str(x) for x in target_series.dropna().unique().tolist()]
        counts = target_series.value_counts(dropna=False).to_dict()
        str_counts = {str(k): int(v) for k, v in counts.items()}
        pcts = {
            str(k): round(int(v) / total_rows * 100, 2)
            for k, v in counts.items()
        }

        target_summary = {
            "target_present": True,
            "unique_values": raw_unique_values,
            "null_target_count": int(target_series.isnull().sum()),
            "distribution_counts": str_counts,
            "distribution_percentages": pcts,
        }
    else:
        target_summary = {
            "target_present": False,
            "error": "Target column 'fraudulent' is missing from dataset.",
        }

    # 4. Leakage columns check
    has_leakage_col = "in_balanced_dataset" in df.columns
    leakage_col_summary = {
        "in_balanced_dataset_present": has_leakage_col,
        "action_required": "Exclude from predictive feature space to prevent data leakage"
        if has_leakage_col
        else "None",
    }

    # 5. Categorical cardinality
    cardinality_summary = {}
    for col in df.columns:
        if df[col].dtype == "object" or df[col].dtype.name == "category":
            cardinality_summary[col] = int(df[col].nunique(dropna=True))

    # 6. Text length statistics for text columns
    text_stats = {}
    for col in TEXT_COLUMNS_OF_INTEREST:
        if col in df.columns:
            text_stats[col] = compute_text_statistics(df[col])

    # 7. Quality observations and flags
    observations = []
    if exact_duplicates_count > 0:
        observations.append(
            f"Found {exact_duplicates_count} ({exact_duplicates_pct}%) exact duplicate rows. "
            f"These must be deduplicated before splitting to prevent train/test leakage."
        )

    if has_leakage_col:
        observations.append(
            "Found 'in_balanced_dataset' column. This metadata field must be excluded "
            "as it introduces ground-truth sampling leakage."
        )

    high_missing = [c for c, s in missing_summary.items() if s["missing_percentage"] > 50.0]
    if high_missing:
        observations.append(
            f"Columns with >50% missing values: {', '.join(high_missing)}. "
            "Missingness patterns may carry predictive signal in fraud detection."
        )

    report: Dict[str, Any] = {
        "file_path": str(resolved_path),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": file_size_mb,
        "detected_encoding": detected_encoding,
        "dimensions": {
            "rows": total_rows,
            "columns": total_cols,
        },
        "column_names": df.columns.tolist(),
        "column_dtypes": {c: str(df[c].dtype) for c in df.columns},
        "missing_values": missing_summary,
        "duplicates": {
            "exact_duplicate_rows": exact_duplicates_count,
            "exact_duplicate_percentage": exact_duplicates_pct,
            "text_subset_duplicate_rows": text_duplicates_count,
        },
        "target_analysis": target_summary,
        "leakage_metadata": leakage_col_summary,
        "categorical_cardinality": cardinality_summary,
        "text_statistics": text_stats,
        "data_quality_observations": observations,
    }

    if output_json_path:
        out_p = Path(output_json_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    return report


def print_inspection_summary(report: Dict[str, Any]) -> None:
    """Print readable inspection report to console."""
    print("=" * 70)
    print("  JobShield AI — EMSCAD Dataset Inspection Report")
    print("=" * 70)
    print(f"File Path:          {report['file_path']}")
    print(f"File Size:          {report['file_size_mb']} MB ({report['file_size_bytes']:,} bytes)")
    print(f"Detected Encoding:  {report['detected_encoding']}")
    print(f"Dataset Dimensions: {report['dimensions']['rows']:,} rows × {report['dimensions']['columns']} columns")
    print("-" * 70)

    print("Target Column Analysis ('fraudulent'):")
    target = report["target_analysis"]
    if target.get("target_present"):
        print(f"  Unique Labels:    {target['unique_values']}")
        print(f"  Null Count:       {target['null_target_count']}")
        print("  Distribution:")
        for label, count in target["distribution_counts"].items():
            pct = target["distribution_percentages"].get(label, 0)
            print(f"    - Label '{label}': {count:,} ({pct}%)")
    else:
        print(f"  ERROR: {target.get('error')}")

    print("-" * 70)
    print("Duplicates & Data Leakage:")
    dup = report["duplicates"]
    print(f"  Exact Duplicate Rows:       {dup['exact_duplicate_rows']:,} ({dup['exact_duplicate_percentage']}%)")
    print(f"  Text Subset Duplicates:     {dup['text_subset_duplicate_rows']:,}")
    print(f"  'in_balanced_dataset' Col:  {report['leakage_metadata']['in_balanced_dataset_present']}")
    print(f"  Leakage Policy:             {report['leakage_metadata']['action_required']}")

    print("-" * 70)
    print("Missing Values Summary (Top Missing Columns):")
    sorted_missing = sorted(
        report["missing_values"].items(),
        key=lambda x: x[1]["missing_percentage"],
        reverse=True,
    )
    for col, stat in sorted_missing[:8]:
        print(f"  - {col:22s}: {stat['missing_count']:,} missing ({stat['missing_percentage']}%)")

    print("-" * 70)
    print("Key Observations:")
    for obs in report["data_quality_observations"]:
        print(f"  [!] {obs}")
    print("=" * 70)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect EMSCAD dataset for JobShield AI fraud detection."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to the raw EMSCAD CSV file (defaults to data/raw/DataSet.csv).",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default="data/processed/dataset_report.json",
        help="Path to write the resulting inspection report JSON.",
    )

    args = parser.parse_args()

    try:
        resolved = resolve_dataset_path(args.data_path)
    except FileNotFoundError as e:
        print(f"\n[ERROR] Dataset not found: {e}", file=sys.stderr)
        return 1

    try:
        report = inspect_dataset(resolved, output_json_path=args.output_report)
        print_inspection_summary(report)
        print(f"\nFull structured report written to: {args.output_report}")
        return 0
    except Exception as exc:
        print(f"\n[ERROR] Failed to inspect dataset: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
