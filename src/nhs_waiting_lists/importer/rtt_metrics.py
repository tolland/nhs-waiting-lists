from pathlib import Path

import pandas as pd
from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import DB_FILE
from nhs_waiting_lists.constants import (
    numeric_cols,
    group_cols,
)
from nhs_waiting_lists.constants import proj_db_path
from nhs_waiting_lists.constants import wait_ranges_gte_18, wait_ranges_lt_18
from nhs_waiting_lists.utils.xdg import XDGBasedir
from sqlalchemy import create_engine
from sqlalchemy import text

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / DB_FILE
FILES_DIR = project_root / "files"

engine = create_engine(f"sqlite:///{DB_PATH}")

"""
NHS RTT Metrics importer
Converts long format to wide format. One row per-provider, per-period, per-specialty
"""


def import_rtt_to_rtt_metrics():
    query = text(
        """
                 SELECT provider_org_code                      AS provider,
                        treatment_function_code                AS treatment,
                        patients_with_unknown_clock_start_date AS unknown_clock_start,
                        *
                 FROM all_rtt_raw
                 ORDER BY provider ASC, treatment ASC, period ASC; \
                 """
    )

    df = pd.read_sql(
        query,
        engine,
    )

    # fuil csv data includes per-commissioning org rows.
    # to reproduce the xlsx data, we sum the per-commissioning-org rows.
    df = (
        df.groupby(group_cols, as_index=False)[numeric_cols]
        .sum()
    )

    df["wait_lt_18"] = df[wait_ranges_lt_18].sum(axis=1, skipna=False)
    df["wait_gte_18"] = df[wait_ranges_gte_18].sum(axis=1, skipna=False)
    df["wait_sum"] = df["wait_lt_18"] + df["wait_gte_18"]
    df["wait_pct_lt_18"] = df["wait_lt_18"] / df["wait_sum"]
    df["wait_diff"] = df["wait_sum"] - df["total_all"]

    df.query("provider == 'RAJ' and treatment == 'C_320' and period == '2025-08'")

    # 2. Pivot to wide form
    df_wide = (
        df.copy()
        .assign(
            rtt_part_type=lambda d: d["rtt_part_type"].map({
                "Part_1A": "admitted",
                "Part_1B": "nonadmitted",
                "Part_2": "incomplete",
                "Part_2A": "incomplete_dta",
                "Part_3": "new_periods",
            })
        )
        .pivot_table(
            index=[
                "period",
                "provider",
                "treatment",
            ],
            columns=["rtt_part_type"],
            values=["total_all", "wait_lt_18", "wait_gte_18", "wait_sum", "wait_diff","wait_pct_lt_18"],
            aggfunc="first"
        )
        .reset_index()
    )
    # df_wide["wait_lt_18"] = df.groupby(["period", "provider", "treatment"])["wait_lt_18"].first().values
    # df_wide["wait_gte_18"] = df.groupby(["period", "provider", "treatment"])["wait_gte_18"].first().values
    # df_wide = df_wide.merge(
    #     df.groupby(["period", "provider", "treatment"])[["wait_lt_18", "wait_gte_18"]].first().reset_index(),
    #     on=["period", "provider", "treatment"]
    # )
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

    print(df_wide.columns)

    df_wide.query("provider == 'RAJ' and treatment == 'C_999' and period == '2025-08'")

    # Nan for treated metrics can be interpreted as 0, which is probably not valid generally
    cols_to_fill: list[str] = ["admitted", "nonadmitted", "incomplete", "new_periods"]
    df_wide[cols_to_fill] = df_wide[cols_to_fill].fillna(0).astype("int64")

    df_wide["incomplete_prev"] = df_wide.groupby(
        ["provider", "treatment"], as_index=False
    )["incomplete"].shift(1)
    df_wide["admitted_prev"] = df_wide.groupby(
        ["provider", "treatment"], as_index=False
    )["admitted"].shift(1)
    df_wide["new_periods_prev"] = df_wide.groupby(
        ["provider", "treatment"], as_index=False
    )["new_periods"].shift(1)
    df_wide["nonadmitted_prev"] = df_wide.groupby(
        ["provider", "treatment"], as_index=False
    )["nonadmitted"].shift(1)

    df_wide["incomplete_diff"] = df_wide["incomplete"] - df_wide["incomplete_prev"]
    df_wide["incomplete_expected"] = (
        df_wide["incomplete_prev"]
        + df_wide["new_periods"]
        - df_wide["nonadmitted"]
        - df_wide["admitted"]
    )
    df_wide["treated"] = df_wide["nonadmitted"] + df_wide["admitted"]
    df_wide["treated_prev"] = df_wide["nonadmitted_prev"] + df_wide["admitted_prev"]

    df_wide["incomplete_expected"] = (
        df_wide["incomplete_prev"]
        + df_wide["new_periods"]
        - df_wide["nonadmitted"]
        - df_wide["admitted"]
    )

    df_wide["untreated"] = df_wide["incomplete"] - df_wide["incomplete_expected"]

    connection = engine.raw_connection()
    cursor = connection.cursor()

    table_name = "consolidated"

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
