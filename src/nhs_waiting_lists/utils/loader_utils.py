import sys
from pathlib import Path

import numpy as np
import pandas as pd

from nhs_waiting_lists.constants import (
    MONTHS,
    all_cols,
    numeric_cols,
    group_cols,
    wait_ranges,
    rtt_base_columns,
)


# utils and constants for processing rtt wtd full csv data
#
# DEPRECATION NOTE: This module contains legacy utilities primarily used in Jupyter notebooks.
# For production code:
# - Use utils2.load_rtt_csv() instead of load_rtt_csv() - it handles CSVFormatSpec properly
# - Use utils2.normalize_measure() for measure normalization
# - Consider migrating notebook functionality to CLI commands

def parse_rtt_period(value: str) -> str:
    _, month_str, year_str = value.split("-")
    month = MONTHS[month_str.upper()]
    return f"{int(year_str):04d}-{month:02d}"


def fiscal_to_calendar(row):
    start_year, end_year = row["Year"].split("-")
    month = MONTHS[row["Period Name"].upper()]
    # April–December belong to start_year, Jan–Mar to end_year
    year = int(start_year) if month >= 4 else int(start_year+1)
    return f"{year:04d}-{month:02d}"

def fix_rtt_period(row):
    if row["Period"].startswith("RTT-"):
        return parse_rtt_period(row["Period"])
    else:
        start_yyyy, end_yy, month = row["Period"].split("-")
        year = int(start_yyyy) if MONTHS[month] >= 4 else (int(start_yyyy) + 1)
        return f"{year:04d}-{MONTHS[month]:02d}"


rtt_csv_key = [
    "Provider Org Code",
    "RTT Part Type",
    "Treatment Function Code",
    "Commissioner Org Code"]

rtt_csv_sample_cols = [
    "Gt 00 To 01 Weeks SUM 1",
    "Total All",
]

def count_lines(filepath: str) -> int:
    with open(filepath, 'r') as f:
        return sum(1 for _ in f)

def load_rtt_csv(
        filepath: Path|str,
        ):
    """DEPRECATED: Use utils2.load_rtt_csv() instead - it handles CSVFormatSpec registry properly."""
    count = count_lines(filepath)
    print(f"Loading {filepath} with {count} lines")
    df = pd.read_csv(
        filepath,
        low_memory=False,
        index_col=rtt_csv_key,
    )
    return df

def clean_wtt_rows(df_source):
    """Load full CSV file into memory."""
    df_source.columns = (df_source.columns
                         .str.strip()
                         .str.lower()
                         .str.replace(" ", "_")
                         .str.replace("[()€$]", "",
                                      regex=True)
                         .str.replace("_sum_1", ""))

    df_source.drop(columns=[
        'provider_parent_org_code',
        'provider_parent_name',
        'commissioner_parent_org_code',
        'commissioner_parent_name',
        'commissioner_org_code',
        'commissioner_org_name',
        'status',
    ],
        inplace=True,
        errors='ignore'
    )

    # sanity checks
    expected = set(all_cols)
    actual = set(df_source.columns)

    missing = expected - actual
    unexpected = actual - expected

    if missing or unexpected:
        print(f"Missing: {sorted(missing)}")
        print(f"Unexpected: {sorted(unexpected)}")
        sys.exit(1)

    df_source = df_source.copy()

    # fuil csv data includes per-commissioning org rows.
    # to reproduce the xlsx data, we sum the per-commissioning-org rows.
    df_source = (
        df_source.groupby(group_cols, as_index=False)[numeric_cols]
        .sum()
    )

    df_result = df_source.copy()

    df_result["wait_sum"] = df_result[wait_ranges].sum(axis=1, skipna=True)

    # Compare to total columns
    df_result["diff_total"] = np.where(
        df_result["rtt_part_type"].isin(["Part_1A", "Part_1B"]),
        df_result["wait_sum"] - df_result["total"],
        np.nan,  # or 0 if you prefer
    )
    df_result["diff_total_all"] = np.where(
        df_result["rtt_part_type"].isin(["Part_3"]),
        np.nan,
        df_result["wait_sum"] - df_result["total_all"] + df_result["patients_with_unknown_clock_start_date"],
    )
    return df_result
