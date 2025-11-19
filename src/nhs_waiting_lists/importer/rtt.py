from pathlib import Path

from sqlalchemy import create_engine

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import proj_db_path, DB_FILE
from nhs_waiting_lists.utils.xdg import XDGBasedir

project_root = Path(XDGBasedir.get_data_dir(__app_name__))

DB_PATH = project_root / proj_db_path / DB_FILE

# Database engine for RTT data imports
# Use: engine = create_engine(f"sqlite:///{DB_PATH}")
# Then: df.to_sql(name="all_rtt_raw", con=engine, if_exists="append", index=False)

"""
NHS RTT Data Importer
Imports RTT waiting times data downloaded from NHS into SQLite database

Import stages:
1. Raw import: CSV → all_rtt_raw table (staging, all columns)
2. QA checks: Verify totals, check for discrepancies
3. Aggregation: all_rtt_raw → all_rtt (group by provider, drop commissioner cols)
4. Consolidation: all_rtt → consolidated (pivot + lag + derived metrics)
"""
