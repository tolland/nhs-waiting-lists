from enum import Enum
from pathlib import Path
from typing import Sequence

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class FormatChoices(str, Enum):
    RICH = "rich"
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    JSONL = "jsonl"
    TABLE = "table"


def find_project_root(markers: Sequence[str] = ('.git', 'pyproject.toml', 'requirements.txt')) -> Path:
    current = Path.cwd()
    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return current
        current = current.parent
    raise FileNotFoundError(f"Could not find any of {markers}")


def get(url: str):
    retry_strategy = Retry(
        total=5,  # Here we configure the max retries
        backoff_factor=5,  # And here we are setting the backoff factor
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],  # These are the status codes we want to retry
        allowed_methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
        ],  # These are the methods we want to retry
    )

    # We pass our Retry object in the max_retries kwarg
    adapter = HTTPAdapter(max_retries=retry_strategy)

    # First we create the Session object
    session = Session()

    # Then we mount the adapter for all http and https traffic
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session.get(url)
