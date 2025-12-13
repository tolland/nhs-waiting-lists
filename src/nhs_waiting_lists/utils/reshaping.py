import re
from typing import List, Dict, Any, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter


# --- Core Analysis Functions ---


def extract_buckets(data_row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transforms a single row of wide bucket data (from SQLAlchemy or DataFrame)
    into a clean, long list of dictionaries for easier analysis.
    """
    bucket_data = []

    # Regex to capture the start and end week from the column names
    # Group 1: Start week (\d+)
    # Group 2: End week (optional, in the non-capturing group (?:_to_(\d+))?)
    pattern = re.compile(r"gt_(\d+)(?:_to_(\d+))?_weeks")

    for key, count in data_row.items():
        # Crucial check: only process buckets with actual counts > 0
        if not key.startswith('gt_') or count is None or count == 0:
            continue

        match = pattern.match(key)
        if match:
            start_week = int(match.group(1))
            end_week_str = match.group(2)

            if end_week_str:
                # Standard bucket (e.g., gt_10_to_11_weeks)
                end_week = int(end_week_str)
                bucket_data.append({
                    'start': start_week,
                    'end': end_week,
                    'count': count,
                    'is_catch_all': False,
                    'label': f"{start_week}-{end_week} weeks"
                })
            else:
                # Catch-all bucket (e.g., gt_104_weeks or legacy gt_52_weeks)
                # end_week_str is None here, so we set end to infinity (right-censored)
                bucket_data.append({
                    'start': start_week,
                    'end': np.inf, # Use infinity to denote open-ended
                    'count': count,
                    'is_catch_all': True,
                    'label': f"{start_week}+ weeks"
                })

    # Sort by start week to ensure cumulative calculations work correctly
    return sorted(bucket_data, key=lambda x: x['start'])


def calculate_imputed_mean_age(df: pd.DataFrame) -> Tuple[float, pd.DataFrame]:
    """
    Calculates the mean waiting time, imputing a value for the catch-all bucket.

    Imputation Strategy: For the open interval [L, inf), the mean is approximated as
    L + (1.5 * W), where L is the starting point and W is the width of the
    immediately preceding interval (which is 1 week for this data).
    """
    df["bucket_width"] = df["end"] - df["start"]
    df["midpoint"] = df["start"] + (df["bucket_width"] / 2)

    catch_all_rows = df[df["is_catch_all"]]
    if not catch_all_rows.empty:
        # Assuming only one catch-all row exists
        catch_all_start = catch_all_rows.iloc[0]["start"]
        # 1.5 multiplier times the preceding 1-week interval width
        imputed_midpoint = catch_all_start + 1.5

        # Replace the midpoint for the catch-all
        df.loc[df["is_catch_all"], "midpoint"] = imputed_midpoint

    total_count = df["count"].sum()
    if total_count == 0:
        return 0.0, df

    weighted_sum = (df["count"] * df["midpoint"]).sum()
    mean_age = weighted_sum / total_count

    return mean_age, df


def prepare_for_kaplan_meier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts grouped bucket data into the required format for Kaplan-Meier analysis:
    (Time T, Event E, Weights W).

    Assumptions for Kaplan-Meier:
    1. An event (treatment completion) occurs at the END of the defined interval.
    2. The catch-all bucket represents RIGHT CENSORING: those individuals were still
       waiting (not treated) when the observation period ended (E=0).
    """
    # Create the T (Time) column: The end point of the interval where the event occurred
    df["T"] = df["end"]

    # Create the E (Event) column: 1 for event (treatment completed), 0 for censoring
    # Only the catch-all is open-ended, so it's the only censored group.
    df["E"] = np.where(df["is_catch_all"], 0, 1)

    # Use the count as the W (Weights) column
    df["W"] = df["count"]

    # For the catch-all, the T value (time of censoring) is the start of the bucket.
    # The record indicates they were still waiting at T = catch_all_start.
    if not df[df["is_catch_all"]].empty:
        df.loc[df["is_catch_all"], "T"] = df[df["is_catch_all"]].iloc[0]["start"]

    # Filter to only include the necessary columns and sort by time T
    return df[["T", "E", "W"]].sort_values("T").reset_index(drop=True)


def run_kaplan_meier_analysis(df_km: pd.DataFrame):
    """
    Runs the full Kaplan-Meier fit, calculates the median, and plots the curve.
    Only runs if LIFELINES_AVAILABLE is True.
    """

    kmf = KaplanMeierFitter()

    # Fit the model using the prepared data
    kmf.fit(
        durations=df_km["T"],
        event_observed=df_km["E"],
        weights=df_km["W"],
        label="Waiting Time Survival Function",
    )

    # Calculate and print the median survival time
    non_parametric_median = kmf.median_survival_time_
    print(
        f"\nNon-parametric Median Survival Time (KM Estimate): {non_parametric_median:.2f} weeks"
    )

    # Plot the survival function
    plt.figure(figsize=(10, 6))
    kmf.plot_survival_function()

    # Add median line for visualization
    plt.axhline(0.5, color="red", linestyle="--", label="Median Survival (50%)")
    plt.axvline(non_parametric_median, color="red", linestyle="--")

    plt.title("Kaplan-Meier Survival Function for Waiting Times")
    plt.xlabel("Time (Weeks)")
    plt.ylabel("Proportion Still Waiting (Survival Probability)")
    plt.legend()
    plt.grid(True, which="both", linestyle=":", linewidth=0.5)
    plt.show()
