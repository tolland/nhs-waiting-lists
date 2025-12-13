from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import proj_db_path, DB_FILE
from nhs_waiting_lists.utils.sqlite_utils import load_data_to_database2
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / DB_FILE
DATA_DIR = project_root / "files"

engine = create_engine(f"sqlite:///{DB_PATH}")

"""
NHS Provider Data Parser
Parses Excel files downloaded from NHS and loads them into SQLite database.
This appears to be part of a data series, in that league tables are regularly
published, but I am not seeing multiple data files for various months.
"""


def load_providers():

    df = pd.read_csv(
        DATA_DIR / 'provider-oversight/nhs-oversight-framework-acute-trust-league-table.csv',
    )

    df = df.rename(columns={
        "Trust_code": "provider",
        "Trust_name": "provider_name",
        "Region": "region_name",
        "Trust_subtype": "subtype",
        "Trust_type": "type",
    })

    df = df.filter(["provider", "provider_name", "region_name", "subtype", "type"])

    connection = engine.raw_connection()

    load_data_to_database2(
        df,
        "provider",
        connection,
    )

    # df.to_sql(
    #     name="provider",
    #     con=engine,
    #     if_exists="replace",
    #     index=False
    # )
