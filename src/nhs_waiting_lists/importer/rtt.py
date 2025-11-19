from pathlib import Path

from sqlalchemy import create_engine

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import proj_db_path
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / "nhs_rttwtd.db"

# Database engine for RTT data imports
# Use: engine = create_engine(f"sqlite:///{DB_PATH}")
# Then: df.to_sql(name="table_name", con=engine, if_exists="replace", index=False)

"""
NHS RTT Data Importer
Imports RTT waiting times data downloaded from NHS into SQLite database
"""
