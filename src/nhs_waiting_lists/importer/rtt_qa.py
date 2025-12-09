import numpy as np
import pandas as pd


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
    wait_cols = [col for col in df.columns if col.startswith("gt_") and "_weeks" in col]
    df["wait_sum"] = df[wait_cols].sum(axis=1, skipna=True)

    # Compute differences for QA
    df["diff_total"] = np.where(
        df["pathway"].isin(["part_1a", "part_1b"]),
        df["wait_sum"] - df.get("total", 0),
        np.nan,
    )
    df["diff_total_all"] = np.where(
        df["pathway"].isin(["part_3"]),
        np.nan,
        df["wait_sum"]
        - df.get("total_all", 0)
        + df.get("unknown_start", 0),
    )

    return df


def check_qa_issues(
    df: pd.DataFrame, period: str, tolerance: float = 0.01
) -> list[str]:
    """
    Check for data quality issues.

    Returns list of issue descriptions (empty if all OK).
    """
    issues = []

    # Check for rows with significant total discrepancies
    bad_total = df[df["diff_total"].abs() > tolerance]
    if len(bad_total) > 0:
        issues.append(
            f"Period {period}: {len(bad_total)} rows with diff_total > {tolerance}"
        )

    bad_total_all = df[df["diff_total_all"].abs() > tolerance]
    if len(bad_total_all) > 0:
        issues.append(
            f"Period {period}: {len(bad_total_all)} rows with diff_total_all > {tolerance}"
        )

    return issues
