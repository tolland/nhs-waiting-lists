import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.utils.olde_excel_mapps import (
    OP_MEASURE_TYPE_VALID_PERMS,
    EXCEL_OP_MAPS,
    NATIONAL_CODES,
    REGIONAL_CODES,
)
from nhs_waiting_lists.utils.utils2 import normalize_measure
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))


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


def process_op_excel(data, year, yr_next, _suffix):
    df_peek = pd.read_excel(
        project_root / "files" / data["path"],
        sheet_name=f"MPDP {year}-{yr_next}",
        nrows=3,
        header=None,
    )

    # print(f"peek: {df_peek}")
    print(f"peek: {df_peek.iloc[0,0]}")
    peeked = df_peek.iloc[0, 0]
    if peeked == "Code":
        skiprows = 0
    else:
        skiprows = 1

    df = pd.read_excel(
        project_root / "files" / data["path"],
        sheet_name=f"MPDP {year}-{yr_next}",
        skiprows=skiprows,
        na_values=["*"],
    )
    print(f"processing {data['path']}")

    df_orig = df.copy()

    df = (
        df.rename(columns={"Code": "organisation_code"}) if "Code" in df.columns else df
    )

    df.columns = (
        df.columns.str.strip()
        .str.replace(":\n", ":")
        .str.replace(": \n", ":")
        .str.replace("–", "-")
    )

    df["reporting_period"] = f"{year}-{yr_next}"

    meta_cols = ["organisation_code", "Description", "reporting_period"]

    df = df.rename(
        columns=EXCEL_OP_MAPS,
        # errors='ignore'
    )
    # print(df.columns)
    value_cols = [c for c in df.columns if c not in meta_cols]

    df = df.melt(
        id_vars=meta_cols,
        value_vars=value_cols,
        var_name="raw_measure",
        value_name="measure_value",
    )

    df["measure_value"] = df["measure_value"].replace("-", np.nan)

    df[["measure_type", "measure"]] = df.raw_measure.str.split(":", expand=True, n=1)

    # initial check to see what will be filtered out
    check_valid_pairs(
        OP_MEASURE_TYPE_VALID_PERMS,
        ["measure_type", "measure"],
        df,
        raise_on_error=False,
    )

    mask_set = df.apply(
        lambda row: (row["measure_type"], row["measure"])
        in set(OP_MEASURE_TYPE_VALID_PERMS),
        axis=1,
    )
    df_filtered = df[mask_set].iloc[:, :]
    # confirm that the filtered set is valid, raise if not
    check_valid_pairs(
        OP_MEASURE_TYPE_VALID_PERMS, ["measure_type", "measure"], df_filtered
    )

    valid_df = pd.DataFrame(
        OP_MEASURE_TYPE_VALID_PERMS, columns=["measure_type", "measure"]
    )
    codes = df_filtered["organisation_code"].unique()

    print(f"filtered codes: {len(codes)}")
    print(f"expected pairs: {len(OP_MEASURE_TYPE_VALID_PERMS)}")
    print(f"expected pairs: {len(OP_MEASURE_TYPE_VALID_PERMS) * len(codes)}")

    expected = (
        valid_df.assign(key=1)
        .merge(
            pd.DataFrame(
                {
                    "organisation_code": df_filtered["organisation_code"].unique(),
                    "key": 1,
                }
            ),
            on="key",
        )
        .drop(columns="key")
    )
    print(f"expected: {len(expected)}")

    # select the actual triplets
    actual = df_filtered[
        ["organisation_code", "measure_type", "measure"]
    ].drop_duplicates()

    # left join to find missing combinations
    missing = expected.merge(actual, how="left", indicator=True)
    missing = missing.loc[missing["_merge"] == "left_only"].drop(columns="_merge")

    if missing.empty:
        print("✅ Every Code has all measure_type/measure combinations.")
    else:
        print(
            f"⚠️ Missing {len(missing)} combinations across {missing['organisation_code'].nunique()} codes."
        )
        print(
            missing.groupby("organisation_code")[["measure_type", "measure"]]
            .apply(lambda g: g.values.tolist())
            .head(10)
        )  # show a sample

    df_filtered["geography_level"] = np.select(
        [
            df_filtered["organisation_code"].isin(NATIONAL_CODES),
            df_filtered["organisation_code"].isin(REGIONAL_CODES),
        ],
        [
            "National",
            "Commissioning Region",
        ],
        default="Provider",
    )

    df_filtered = df_filtered[
        [
            "reporting_period",
            "geography_level",
            "organisation_code",
            "measure_type",
            "measure",
            "measure_value",
        ]
    ]

    return df_orig, df_filtered


GEO_MAP = {
    "01.National": "National",
    "02.Commissioning Region": "Commissioning Region",
    "03.Provider": "Provider",
    "National": "National",
    "Commissioning Region": "Commissioning Region",
    "Provider": "Provider",
}

AGE_GROUP_TYPES = {
    "Attended Appointments by Age Group",
    "Did not Attend by Age Group",
}


def process_op_csv(data, year, yr_next):
    df = pd.read_csv(
        project_root / "files" / data["path"],
        na_values=["*"],
        # converters={"REPORTING_PERIOD": two_years_to_nhs_year}
    )
    df_orig = df.copy()

    df["REPORTING_PERIOD"] = f"{year}-{yr_next}"
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("[()€$]", "", regex=True)
        .str.replace("_sum_1", "")
    )

    df.drop(
        columns=[
            "organisation_description",
        ],
        inplace=True,
    )
    # df = df.assign(REPORTING_PERIOD=lambda x: (x['Field_1'] * x['Field_2'] * x['Field_3']))
    df["geography_level"] = df["geography_level"].map(GEO_MAP)

    mask = df["measure"].eq("Oct-19") & df["measure_type"].isin(AGE_GROUP_TYPES)

    df.loc[mask, "measure"] = "10-19"

    df["measure"] = df["measure"].apply(normalize_measure)

    print(df.dtypes)
    print(df.tail())
    return df_orig, df


op_pla_file = r"hosp-epis-stat-outp-pla-([0-9]{4})-([0-9]{2})-(?:data|tab(?:%20v2)?)\.(csv|xlsx?m?)"


def process_op_file(data):
    match = re.search(op_pla_file, data["filename"])
    if not match:
        print(f"no match for {data['filename']}")
        return

    year, yr_next, suffix = match.groups()
    print(f"year: {year}, yr_next: {yr_next} suffix: {suffix}")
    if suffix == "xlsx":
        df_orig, df = process_op_excel(data, year, yr_next, suffix)
    else:  #  suffix == "csv"
        df_orig, df = process_op_csv(data, year, yr_next)

    if isinstance(df, pd.DataFrame):
        # load_data_to_database2(df, "outpatients_activity", connection)

        return df_orig, df


def check_valid_pairs(valid_perms, colnames, target_df, raise_on_error=True):
    """
    The current series of outpatient activity data has a valid set of measure_type / measure combinations. This method is used to check that
    the old data that was restructured into the new format is still valid.

    :param valid_perms: List of valid measure_type/measure combinations
    :param colnames: Column names for the valid_perms DataFrame
    :param target_df: DataFrame to validate against valid combinations
    :param raise_on_error: If True (default), raises ValueError when data integrity issues are found.
                          If False, only prints warnings and returns without raising.
    :return: None
    :raises ValueError: When data integrity issues are found and raise_on_error=True
    """
    valid_df = pd.DataFrame(valid_perms, columns=colnames)
    valid_set = set(OP_MEASURE_TYPE_VALID_PERMS)

    current_pairs = set(zip(target_df["measure_type"], target_df["measure"]))

    missing = valid_set - current_pairs
    extra = current_pairs - valid_set

    if missing or extra:
        error_msg = "Data integrity issues detected:"
        if missing:
            error_msg += f"\n  Missing pairs ({len(missing)}):"
            for mt, m in sorted(missing):
                error_msg += f"\n    {mt} → {m}"
        if extra:
            error_msg += f"\n  Unexpected pairs ({len(extra)}):"
            for mt, m in sorted(extra):
                error_msg += f"\n    {mt} → {m}"

        print(f"⚠️ {error_msg}")

        if raise_on_error:
            raise ValueError(error_msg)
    else:
        print("✅ All measure_type / measure combinations are present and valid.")


op_melt_map = {
    "Table 1": "Attendance Summary by Gender",
    "Table 2": "Attendance Type",
    "Table 2a": "Attendances",
    "Table 3": "Attendances by selected main specialty",
    "Table 4": "Attended Appointments by Age Group",
    "Table 5": "Did not Attend by Age Group",
    "Table 6": "First Att from GP & Dental Practitioner refs by Waiting Time",
    "Table 7": "First Attendances by Outcome",
    "Table 8": "First Attendances by Source of Referral",
}

# normalize_measure2 was removed - it was a duplicate of normalize_measure from utils2.py
# which is already imported at the top of this file

XLS_TO_CSV_COLS = {
    "Attendance Summary by Gender": {
        "Attendances - Males": "Attendance-Male",
        "": "Attended first tele consultation",
        # "Attended subsequent appointment",
        # "Attended subsequent tele consultation",
        # "Attended but first/subsequent/tele unknown",
        # "Did not attend first appointment",
        # "Did not attend first tele consultation",
        # "Did not attend subsequent appointment",
    }
}
