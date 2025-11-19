from pathlib import Path

from .nhs_ctl_core import NhsCtlCore

def ensure_data_downloaded():
    cache_dir = Path("~/.cache/waiting_lists")
    db_path = cache_dir / "data.db"
    if not db_path.exists():
        # download_from_s3_or_wherever(db_path)
        pass
    return db_path

