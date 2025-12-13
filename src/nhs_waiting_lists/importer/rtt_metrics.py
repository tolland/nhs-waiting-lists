from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text, bindparam

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import DB_FILE, map_names
from nhs_waiting_lists.constants import (
    numeric_cols,
    group_cols,
)
from nhs_waiting_lists.constants import proj_db_path
from nhs_waiting_lists.constants import wait_ranges_gte_18, wait_ranges_lt_18
from nhs_waiting_lists.utils.date_field_parsing import previous_period
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / DB_FILE
FILES_DIR = project_root / "files"

engine = create_engine(f"sqlite:///{DB_PATH}")

"""
NHS RTT Metrics importer
Converts long format to wide format. One row per-provider, per-period, per-specialty
"""


def import_rtt_to_rtt_metrics(
    start_period: Optional[str] = "1990-01",
    end_period: Optional[str] = "2099-12",
    check_only: bool = False,
):

    # need to go one further back for diff metrics
    # this makes importing a bit fragile, @TODO fix this
    prev_period = previous_period(start_period)

    query = text(
        """
        SELECT *
        FROM all_rtt_raw
        WHERE period >= :start_period
          AND period <= :end_period
        ORDER BY provider, treatment, period; \
        """
    ).bindparams(
        bindparam("start_period", expanding=False),
        bindparam("end_period", expanding=False),
    )

    df = pd.read_sql(
        query,
        engine,
        params={
            "start_period": prev_period,
            "end_period": end_period,
        },
    )

    print(f"Loaded {len(df)} rows from all_rtt_raw")
    pd.set_option("display.max_columns", None)
    # print(f"Col names: {df.columns}")
    # print(df.head())
    all_columns = list(df.columns)
    print("All column names:")
    print(all_columns)

    # fuil csv data includes per-commissioning org rows.
    # to reproduce the xlsx data, we sum the per-commissioning-org rows.
    df = df.groupby(group_cols, as_index=False)[numeric_cols].sum()

    # @TODO somewhere these are being coerced to zero, rather than NaN
    # this is messing up the wait_sum calculation
    df["wait_lt_18"] = np.where(
        df["pathway"].isin(["new_periods"]),
        np.nan,
        df[wait_ranges_lt_18].sum(axis=1, skipna=True, min_count=1),
    )
    df["wait_gte_18"] = np.where(
        df["pathway"].isin(["new_periods"]),
        np.nan,
        df[wait_ranges_gte_18].sum(axis=1, skipna=True, min_count=1),
    )

    df["wait_sum"] = df["wait_lt_18"] + df["wait_gte_18"]

    df.loc[df["wait_sum"] == 0, "wait_sum"] = np.nan
    df["wait_pct_lt_18"] = df["wait_lt_18"] / df["wait_sum"]

    df["wait_diff"] = df["total_all"] - df["unknown_start"] - df["wait_sum"]

    # Debug: check for non-zero wait_diff
    non_zero_mask = df["wait_diff"].notna() & (df["wait_diff"] != 0)
    if non_zero_mask.any():
        offending_rows = df[non_zero_mask].head(5)
        print("Offending rows with non-zero wait_diff:")
        print(
            offending_rows[
                [
                    "provider",
                    "treatment",
                    "period",
                    "pathway",
                    "wait_sum",
                    "total_all",
                    "wait_diff",
                    "unknown_start",
                ]
            ]
        )
        raise ValueError(f"Found {non_zero_mask.sum()} rows with non-zero wait_diff")

    # 2. Pivot to wide form

    all_columns = list(df.columns)
    print("All df column names:")
    print(all_columns)

    df_wide = df.pivot_table(
        index=[
            "period",
            "provider",
            "treatment",
        ],
        columns=["pathway"],
        values=[
            "total_all",
            "wait_lt_18",
            "wait_gte_18",
            "wait_sum",
            "wait_diff",
            "wait_pct_lt_18",
        ],
        aggfunc="first",
    ).reset_index()

    all_columns = list(df_wide.columns)
    print("All df_wide column names:")
    print(all_columns)

    cols_to_drop = [
        col
        for col in df_wide.columns
        if col[0]
        in ["wait_lt_18", "wait_gte_18", "wait_sum", "wait_diff", "wait_pct_lt_18"]
        and col[1] != "incomplete"
    ]

    df_wide = df_wide.drop(columns=cols_to_drop)

    # Rename to flatten
    df_wide.columns = [
        "_".join(col).strip("_") if col[1] else col[0] for col in df_wide.columns.values
    ]

    df_wide = df_wide.rename(
        columns={
            "total_all_admitted": "admitted",
            "total_all_incomplete": "incomplete",
            "total_all_incomplete_dta": "incomplete_dta",
            "total_all_new_periods": "new_periods",
            "total_all_nonadmitted": "nonadmitted",
            "wait_diff_incomplete": "wait_diff",
            "wait_gte_18_incomplete": "wait_gte_18",
            "wait_lt_18_incomplete": "wait_lt_18",
            "wait_sum_incomplete": "wait_sum",
            "wait_pct_lt_18_incomplete": "wait_pct_lt_18",
        }
    )

    print("All df_wide column names2:")
    print(df_wide.columns)

    # Nan for treated metrics can be interpreted as 0, which is probably not valid generally
    cols_to_fill: list[str] = ["admitted", "nonadmitted", "incomplete", "new_periods"]
    df_wide[cols_to_fill] = df_wide[cols_to_fill].fillna(0).astype("int64")

    df_wide["incomplete_prev"] = df_wide.groupby(
        ["provider", "treatment"], as_index=False
    )["incomplete"].shift(1)

    # these are probably unnecessary, only lagged imcompletes is useful
    df_wide["admitted_prev"] = df_wide.groupby(
        ["provider", "treatment"], as_index=False
    )["admitted"].shift(1)

    df_wide["new_periods_prev"] = df_wide.groupby(
        ["provider", "treatment"], as_index=False
    )["new_periods"].shift(1)

    df_wide["nonadmitted_prev"] = df_wide.groupby(
        ["provider", "treatment"], as_index=False
    )["nonadmitted"].shift(1)

    # Total treatable is used for proportions of activity metrics potentials
    df_wide["total_treatable"] = (
        df_wide["incomplete_prev"] + df_wide["new_periods"]
    )

    df_wide["incomplete_diff"] = df_wide["incomplete"] - df_wide["incomplete_prev"]
    df_wide["incomplete_expected"] = (
        df_wide["incomplete_prev"]
        + df_wide["new_periods"]
        - df_wide["nonadmitted"]
        - df_wide["admitted"]
    )
    df_wide["completed"] = df_wide["nonadmitted"] + df_wide["admitted"]
    df_wide["completed_prev"] = df_wide["nonadmitted_prev"] + df_wide["admitted_prev"]

    # df_wide["pathway_delta"] = df_wide["new_periods"]- df_wide["completed"]

    df_wide["incomplete_expected"] = (
        df_wide["incomplete_prev"]
        + df_wide["new_periods"]
        - df_wide["completed"]
    )

    df_wide["untreated"] = df_wide["incomplete"] - df_wide["incomplete_expected"]

    print("All df_wide column names3:")
    print(df_wide.columns)

    # Drop the extra "previous-period" rows
    df_wide = df_wide[df_wide["period"] != previous_period(start_period)]

    connection = engine.raw_connection()
    cursor = connection.cursor()

    table_name = "consolidated"

    # Get column names
    columns = list(df_wide.columns)
    placeholders = ", ".join(["?" for _ in columns])
    column_names = ", ".join(columns)

    # Insert data row by row using INSERT OR REPLACE
    for _, row in df_wide.iterrows():
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
    print(f"Loaded {len(df_wide)} rows into {table_name}")
