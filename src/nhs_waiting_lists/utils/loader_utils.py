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
