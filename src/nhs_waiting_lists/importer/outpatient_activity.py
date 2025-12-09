from pathlib import Path
from typing import Optional

import numpy as np
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
NHS Outpatients Activity raw data importer
"""


def import_outpatient_activity_period(
    period: str,
    check_only: bool = False,
):
    period_date = datetime.strptime(period, "%Y-%m").date()
