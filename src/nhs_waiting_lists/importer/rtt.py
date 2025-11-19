import sqlite3
from pathlib import Path

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import proj_db_path
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / "nhs_rttwtd.db"


conn = sqlite3.connect(DB_PATH)

"""
NHS Provider Data Parser
Parses Excel files downloaded from NHS and loads them into SQLite database
"""
