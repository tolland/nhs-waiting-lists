from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text, bindparam

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import DB_FILE, wait_ranges
from nhs_waiting_lists.constants import (
    numeric_cols,
    group_cols,
)
from nhs_waiting_lists.constants import proj_db_path
from nhs_waiting_lists.constants import wait_ranges_gte_18, wait_ranges_lt_18
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / DB_FILE
FILES_DIR = project_root / "files"

engine = create_engine(f"sqlite:///{DB_PATH}")

"""
NHS RTT Pathways importer
For convenience, (this should probably be a view or something) I am putting
the different pathways into a single table.
"""


def import_rtt_to_rtt_pathways(
    start_period: Optional[str] = "1990-01",
    end_period: Optional[str] = "2099-12",
    check_only: bool = False,
):

    if not start_period:
        start_period = "1990-01"

    if not end_period:
        end_period = "2099-12"

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
    print(f"in the import_rtt_to_rtt_pathways method {start_period=} {end_period=}")

    df = pd.read_sql(
        query,
        engine,
        params={
            "start_period": start_period,
            "end_period": end_period,
        },
    )
    print(f"length: {len(df)}")

    # fuil csv data includes per-commissioning org rows.
    # to reproduce the xlsx data, we sum the per-commissioning-org rows.
    df = df.groupby(group_cols, as_index=False)[numeric_cols].sum()

    # @TODO somewhere these are being coerced to zero, rather than NaN
    # this is messing up the wait_sum calculation. this is probably out of date
    # as trying to use nullable int type was not working. we probably need np nullable float
    # everywhere and cast on the way out.
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

    df["qa_wait_sum"] = df["wait_lt_18"] + df["wait_gte_18"]

    df.loc[df["qa_wait_sum"] == 0, "qa_wait_sum"] = np.nan
    df["wait_pct_lt_18"] = df["wait_lt_18"] / df["qa_wait_sum"]
    df["wait_pct_gte_18"] = df["wait_gte_18"] / df["qa_wait_sum"]

    df["qa_wait_diff"] = df["total_all"] - df["unknown_start"] - df["qa_wait_sum"]

    # Debug: check for non-zero wait_diff
    non_zero_mask = df["qa_wait_diff"].notna() & (df["qa_wait_diff"] != 0)
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
                    "total_all",
                    "unknown_start",
                    "qa_wait_diff",
                    "qa_wait_sum",
                ]
            ]
        )
        raise ValueError(f"Found {non_zero_mask.sum()} rows with non-zero wait_diff")

    all_columns = list(df.columns)
    print("All df column names:")
    print(all_columns)

    # handle incomplete records

    incomplete_df = df.query("pathway == 'incomplete'").drop(
        columns=[
            "total",
            "unknown_start",
            "pathway",
        ]
    )
    print(incomplete_df.head())
    print(f"length: {len(incomplete_df)}")

    import_rtt_to_rtt_pathways_do_sql(
        incomplete_df,
        "incomplete",
    )

    # handle new periods

    new_periods_df = df.query("pathway == 'new_periods'").drop(
        columns=[
            "total",
            "unknown_start",
            "pathway",
            "wait_lt_18",
            "wait_gte_18",
            "wait_pct_lt_18",
            "wait_pct_gte_18",
                    "qa_wait_diff",
                    "qa_wait_sum",
        ]
        + wait_ranges
    )

    import_rtt_to_rtt_pathways_do_sql(
        new_periods_df,
        "new_periods",
    )

    # handle admitted records

    admitted_df = df.query("pathway == 'admitted'").drop(
        columns=[
            "pathway",
        ]
    )
    print(admitted_df.head())
    print(f"length: {len(admitted_df)}")

    import_rtt_to_rtt_pathways_do_sql(
        admitted_df,
        "admitted",
    )

    # handle nonadmitted records

    nonadmitted_df = df.query("pathway == 'nonadmitted'").drop(
        columns=[
            "pathway",
        ]
    )
    print(nonadmitted_df.head())
    print(f"length: {len(nonadmitted_df)}")

    import_rtt_to_rtt_pathways_do_sql(
        nonadmitted_df,
        "nonadmitted",
    )


def import_rtt_to_rtt_pathways_do_sql(df: pd.DataFrame, table_name: str) -> None:

    connection = engine.raw_connection()
    cursor = connection.cursor()

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
