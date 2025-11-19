

import sys
from pathlib import Path
from typing import Sequence


def find_project_root(markers: Sequence[str] = ('.git', 'pyproject.toml', 'requirements.txt')) -> Path:
    current = Path.cwd()
    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return current
        current = current.parent
    raise FileNotFoundError(f"Could not find any of {markers}")
