from pathlib import Path

from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import (
    proj_db_path,
    DB_FILE,
    proj_data_path,
    proj_files_path,
)
from nhs_waiting_lists.utils.xdg import XDGBasedir


def get_db_path() -> Path:
    project_root = Path(XDGBasedir.get_data_dir(__app_name__))
    DB_PATH = project_root / proj_db_path / DB_FILE

    return DB_PATH

def get_db_dir() -> Path:
    project_root = Path(XDGBasedir.get_data_dir(__app_name__))
    return project_root / proj_db_path

def get_data_dir() -> Path:
    project_root = Path(XDGBasedir.get_data_dir(__app_name__))
    return project_root / proj_data_path

def get_files_dir() -> Path:
    project_root = Path(XDGBasedir.get_data_dir(__app_name__))
    return project_root / proj_files_path

def init_paths():
    get_db_dir().mkdir(parents=True, exist_ok=True)
    get_data_dir().mkdir(parents=True, exist_ok=True)
    get_files_dir().mkdir(parents=True, exist_ok=True)
