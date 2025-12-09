import json
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import (
    proj_db_path,
    DB_FILE,
    map_names,
)
from nhs_waiting_lists.importer.rtt_qa import compute_qa_columns, check_qa_issues
from nhs_waiting_lists.utils.csv_format_spec import RTTFormatRegistry
from nhs_waiting_lists.utils.date_field_parsing import fix_rtt_period
from nhs_waiting_lists.utils.sqlite_utils import (
    calculate_optimal_chunksize,
    get_sqlite_max_variables,
)
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / DB_FILE
FILES_DIR = project_root / "files"

engine = create_engine(f"sqlite:///{DB_PATH}")


def load_rtt_csv_from_zip(
    zip_path: Path, period: str, registry: RTTFormatRegistry
) -> pd.DataFrame:
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

    # Get format spec
    # @TODO don't fallback, it hides errors.
    spec = registry.get_spec_with_fallback(zip_path, period_date)

    print(f"  Format detected: {spec.format_name}")

    # Extract and read CSV from zip
    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_files = [name for name in zf.namelist() if name.endswith(".csv")]
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

    if spec.cols_to_drop:
        df.drop(columns=spec.cols_to_drop, inplace=True)


    df = df.copy().assign(pathway=lambda d: d["pathway"].map(map_names))

    # fix mangled dates in Period column
    df["Period"] = df.apply(fix_rtt_period, axis=1)

    # Clean column names
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("[()€$]", "", regex=True)
        .str.replace("_sum_1", "")
        .str.replace("_sum", "")
    )

    return df


def import_rtt_period(
    period: str, file_path: Path, registry: RTTFormatRegistry, check_only: bool = False
) -> Optional[pd.DataFrame]:
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
    print(f"Importing period {period}: {file_path.name}")

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
            raise ValueError(
                error_msg
                + "\n  Refusing to import data with QA issues. Fix source data or adjust tolerance."
            )

    if check_only:
        print(f"  ✓ QA check complete (no issues)")
        return df

    # Import to database with optimized bulk insert
    num_columns = len(df.columns)
    chunksize = calculate_optimal_chunksize(num_columns)
    max_vars = get_sqlite_max_variables()

    print(
        f"  Bulk insert: {num_columns} columns, chunksize={chunksize} (SQLite limit: {max_vars} variables)"
    )

    # df.to_sql(
    #     name="all_rtt_raw",
    #     con=engine,
    #     if_exists="append",
    #     index=False,
    #     method="multi",
    #     chunksize=chunksize,
    # )
    connection = engine.raw_connection()
    cursor = connection.cursor()

    table_name = "all_rtt_raw"

    # Get column names
    columns = list(df.columns)
    placeholders = ", ".join(["?" for _ in columns])
    column_names = ", ".join(columns)

    # Insert data row by row using INSERT OR REPLACE
    for _, row in df.iterrows():
        values = [row[col] for col in columns]
        insert_sql = f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"
        try:
            cursor.execute(insert_sql, values)
        except Exception as e:
            print(
                f"Error inserting row: {e} query : {insert_sql} values: {values} row: {row}"
            )
            cursor.close()
            raise e

    connection.commit()
    print(f"Loaded {len(df)} rows into {table_name}")

    print(f"  ✓ Imported {len(df):,} rows")
    return None


def import_all_rtt_from_jsonl(
    jsonl_path: Optional[Path] = None,
    start_period: Optional[str] = None,
    end_period: Optional[str] = None,
    check_only: bool = False,
):
    """
    Import all RTT data using scrapy JSONL metadata file to locate previously
     downloaded files.

    Args:
        jsonl_path: Path to JSONL file (default: files/downloadsrtt-waiting-times.jsonl)
        start_period: Optional start period filter (YYYY-MM)
        end_period: Optional end period filter (YYYY-MM)
        check_only: If True, only run QA checks without importing
    """
    if jsonl_path is None:
        jsonl_path = FILES_DIR / "downloads_rtt-waiting-times.jsonl"

    if not jsonl_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")

    registry = RTTFormatRegistry()

    print(f"Reading metadata from: {jsonl_path}")
    print(f"Database: {DB_PATH}")
    print()

    imported_count = 0
    skipped_count = 0

    with open(jsonl_path, "r") as f:
        for line in f:
            data = json.loads(line)

            # Deduplicate files by source URL (preserve first occurrence)
            files = data.get("files", [])
            unique_files = []
            seen_urls = set()
            for fm in files:
                url = fm.get("url")
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_files.append(fm)

            for file_meta in unique_files:
                period = file_meta.get("period")
                if not period:
                    continue

                # Apply period filters
                if start_period and period < start_period:
                    skipped_count += 1
                    continue
                if end_period and period > end_period:
                    skipped_count += 1
                    continue

                print(
                    f"Processing {period} ({start_period}/{end_period}): {file_meta.get('filename')}"
                )

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
