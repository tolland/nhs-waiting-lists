from sqlalchemy import create_engine

from nhs_waiting_lists.constants import proj_db_path, DB_FILE
from nhs_waiting_lists.utils.proj_paths import find_project_root

project_root = find_project_root()
DB_PATH = project_root / proj_db_path / DB_FILE
DATA_DIR = "./data"


class ConnTrack:
    rttwtd_conn = None

    def __init__(self):
        pass

    @classmethod
    def get_rttwtd_conn(
        cls,
    ):

        if cls.rttwtd_conn:
            return cls.rttwtd_conn

        cls.rttwtd_conn = create_engine(f"sqlite:///{DB_PATH}")
        return cls.rttwtd_conn
