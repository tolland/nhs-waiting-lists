from typing import Optional
import pandas as pd
from typing import Optional

import pandas as pd


def find_data_start_row(df: pd.DataFrame) -> Optional[int]:
    """
    Find the row where actual data starts by looking for 'Region Code' in column B (index 1).
    Returns the row index or None if not found.
    """
    for idx, row in df.iterrows():
        # Check if column B (index 1) contains 'Region Code'
        if pd.notna(row.iloc[1]) and str(row.iloc[1]).strip() == "Trust Code":
            return idx
    return None


def clean_column_name(col_name: str) -> str:
    """Clean a single column name to be SQL-safe"""
    if pd.isna(col_name):
        return "unknown_column"

    clean_col = str(col_name).strip()

    # Replace spaces and special characters with underscores
    clean_col = clean_col.replace(" ", "_").replace("(", "").replace(")", "")
    clean_col = clean_col.replace("-", "_").replace("/", "_").replace("\\", "_")
    clean_col = clean_col.replace("%", "pct").replace("+", "plus")

    # Handle numbers at the start
    if clean_col and clean_col[0].isdigit():
        clean_col = f"col_{clean_col}"

    # Remove multiple consecutive underscores
    import re

    clean_col = re.sub(r"_+", "_", clean_col)

    # Remove leading/trailing underscores
    clean_col = clean_col.strip("_")

    # Ensure it's not empty
    if not clean_col:
        clean_col = "unknown_column"

    return clean_col
