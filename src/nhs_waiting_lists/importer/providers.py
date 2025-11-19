import sqlite3
from pathlib import Path

import pandas as pd

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import proj_db_path
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / "provider_raw.db"
DATA_DIR = project_root / "data"

conn = sqlite3.connect(DB_PATH)

"""
NHS Provider Data Parser
Parses Excel files downloaded from NHS and loads them into SQLite database
"""


def load_providers():

    df = pd.read_csv(
        DATA_DIR / 'nhs-oversight-framework-acute-trust-league-table.csv',
    )

    df = df.rename(columns={
        "Trust_code": "provider_code",
        "Trust_name": "provider_name",
        "Region": "region_name",
        "Trust_subtype": "subtype",
        "Trust_type": "type",
    })

    df.to_sql(
        name="providers",
        con=conn,
        if_exists="replace",
        index=False
    )