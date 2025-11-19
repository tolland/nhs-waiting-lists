import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import proj_db_path, DB_FILE, group_cols, numeric_cols, wait_ranges
from nhs_waiting_lists.utils.xdg import XDGBasedir
from nhs_waiting_lists.utils.csv_format_spec import RTTFormatRegistry

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / DB_FILE
FILES_DIR = project_root / "files"

engine = create_engine(f"sqlite:///{DB_PATH}")

"""
NHS RTT Data Importer
Imports RTT waiting times data downloaded from NHS into SQLite database

Import stages:
1. Raw import: CSV → all_rtt_raw table (staging, all columns)
2. QA checks: Verify totals, check for discrepancies
3. Aggregation: all_rtt_raw → all_rtt (group by provider, drop commissioner cols)
4. Consolidation: all_rtt → consolidated (pivot + lag + derived metrics)
"""


def load_rtt_csv_from_zip(zip_path: Path, period: str, registry: RTTFormatRegistry) -> pd.DataFrame:
    """
    Load RTT CSV from a zip file with format auto-detection.

    Args:
        zip_path: Path to zipped CSV file
        period: Period string in YYYY-MM format (from scrapy metadata)
        registry: RTTFormatRegistry for format detection

    Returns:
        DataFrame with normalized column names
    """
    # Convert period to date for registry lookup
    period_date = datetime.strptime(period, "%Y-%m").date()

    # Get format spec with fallback to file detection
    spec = registry.get_spec_with_fallback(zip_path, period_date)

    print(f"  Format detected: {spec.format_name}")

    # Extract and read CSV from zip
    with zipfile.ZipFile(zip_path, 'r') as zf:
        csv_files = [name for name in zf.namelist() if name.endswith('.csv')]
        if not csv_files:
            raise ValueError(f"No CSV file found in {zip_path}")

        csv_name = csv_files[0]
        with zf.open(csv_name) as f:
            df = pd.read_csv(f, **spec.to_read_csv_kwargs(), low_memory=False)

    # Apply column mapping if specified
    if spec.column_mapping:
        df = df.rename(columns=spec.column_mapping)

    if spec.column_concat:
        for col, cols in spec.column_concat.items():
            df[col] = df[cols].astype(str).agg("-".join, axis=1)
            df.drop(columns=cols, inplace=True)

    # Clean column names
    df.columns = (df.columns
                  .str.strip()
                  .str.lower()
                  .str.replace(" ", "_")
                  .str.replace("[()€$]", "", regex=True)
                  .str.replace("_sum_1", ""))

    return df


def compute_qa_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add QA validation columns to check data integrity.

    Computes:
    - wait_sum: Sum of all waiting time buckets
    - diff_total: wait_sum - total (should be ~0 for Part_1A, Part_1B)
    - diff_total_all: wait_sum - total_all + unknown (should be ~0)
    """
    df = df.copy()

    # Sum all waiting time buckets
    wait_cols = [col for col in df.columns if col.startswith('gt_') and '_weeks' in col]
    df["wait_sum"] = df[wait_cols].sum(axis=1, skipna=True)

    # Compute differences for QA
    df["diff_total"] = np.where(
        df["rtt_part_type"].isin(["part_1a", "part_1b"]),
        df["wait_sum"] - df.get("total", 0),
        np.nan,
    )
    df["diff_total_all"] = np.where(
        df["rtt_part_type"].isin(["part_3"]),
        np.nan,
        df["wait_sum"] - df.get("total_all", 0) + df.get("patients_with_unknown_clock_start_date", 0),
    )

    return df


def check_qa_issues(df: pd.DataFrame, period: str, tolerance: float = 0.01) -> list[str]:
    """
    Check for data quality issues.

    Returns list of issue descriptions (empty if all OK).
    """
    issues = []

    # Check for rows with significant total discrepancies
    bad_total = df[df["diff_total"].abs() > tolerance]
    if len(bad_total) > 0:
        issues.append(f"Period {period}: {len(bad_total)} rows with diff_total > {tolerance}")

    bad_total_all = df[df["diff_total_all"].abs() > tolerance]
    if len(bad_total_all) > 0:
        issues.append(f"Period {period}: {len(bad_total_all)} rows with diff_total_all > {tolerance}")

    return issues


def import_rtt_period(period: str, file_path: Path, registry: RTTFormatRegistry, check_only: bool = False) -> Optional[pd.DataFrame]:
    """
    Import RTT data for a single period.

    Args:
        period: Period in YYYY-MM format
        file_path: Path to zipped CSV file
        registry: RTTFormatRegistry for format detection
        check_only: If True, only run QA checks without importing

    Returns:
        DataFrame if check_only=True, None otherwise
    """
    print(f"Processing {period}: {file_path.name}")

    # Load CSV with format detection
    df = load_rtt_csv_from_zip(file_path, period, registry)

    # Add QA columns
    df = compute_qa_columns(df)

    # Run QA checks
    issues = check_qa_issues(df, period)
    if issues:
        error_msg = f"  ❌ QA Issues found in {period}:\n"
        for issue in issues:
            error_msg += f"    - {issue}\n"

        if check_only:
            print(error_msg)
            print(f"  ✓ QA check complete (issues found)")
            return df
        else:
            # Fail fast - do not import data with QA issues
            raise ValueError(error_msg + "\n  Refusing to import data with QA issues. Fix source data or adjust tolerance.")

    if check_only:
        print(f"  ✓ QA check complete (no issues)")
        return df

    # Import to database
    df.to_sql(
        name="all_rtt_raw",
        con=engine,
        if_exists="append",
        index=False
    )

    print(f"  ✓ Imported {len(df):,} rows")
    return None


def import_all_rtt_from_jsonl(
    jsonl_path: Optional[Path] = None,
    start_period: Optional[str] = None,
    end_period: Optional[str] = None,
    check_only: bool = False
):
    """
    Import all RTT data from scrapy JSONL metadata file.

    Args:
        jsonl_path: Path to JSONL file (default: files/downloadsrtt-waiting-times.jsonl)
        start_period: Optional start period filter (YYYY-MM)
        end_period: Optional end period filter (YYYY-MM)
        check_only: If True, only run QA checks without importing
    """
    if jsonl_path is None:
        jsonl_path = FILES_DIR / "downloadsrtt-waiting-times.jsonl"

    if not jsonl_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")

    registry = RTTFormatRegistry()

    print(f"Reading metadata from: {jsonl_path}")
    print(f"Database: {DB_PATH}")
    print()

    imported_count = 0
    skipped_count = 0

    with open(jsonl_path, 'r') as f:
        for line in f:
            data = json.loads(line)

            for file_meta in data.get("files", []):
                period = file_meta.get("period")
                if not period:
                    continue

                print(f"Processing {period}: {file_meta.get('filename')}")

                # Apply period filters
                if start_period and period < start_period:
                    skipped_count += 1
                    continue
                if end_period and period > end_period:
                    skipped_count += 1
                    continue

                # Get file path from scrapy metadata
                # Scrapy stores downloaded files with hash-based names
                # We need to find the actual file
                file_path = FILES_DIR / file_meta.get("path", "")
                if not file_path.exists():
                    # Try alternative: look for file with period in name
                    pattern = f"*{period}*.zip"
                    matches = list(FILES_DIR.glob(pattern))
                    if matches:
                        file_path = matches[0]
                    else:
                        # Fail fast - missing data file
                        raise FileNotFoundError(
                            f"❌ File not found for period {period}\n"
                            f"  Expected: {FILES_DIR / file_meta.get('path', '')}\n"
                            f"  Searched pattern: {FILES_DIR}/{pattern}\n"
                            f"  Ensure scrapy download completed successfully."
                        )

                import_rtt_period(period, file_path, registry, check_only=check_only)
                imported_count += 1

    print()
    print(f"{'Checked' if check_only else 'Imported'}: {imported_count} periods")
    if skipped_count > 0:
        print(f"Skipped: {skipped_count} periods")
    print(f"Database: {DB_PATH}")
