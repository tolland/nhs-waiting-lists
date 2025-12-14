
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

"""
Pytest configuration and shared fixtures for NHS waiting lists package tests.
"""

# Fixture to set XDG_STATE_HOME to a temp directory
@pytest.fixture
def xdg_state_home(tmp_path: Path, monkeypatch):
    """
    Sets the XDG_STATE_HOME environment variable to a
    temporary directory provided by tmp_path.
    """

    # 1. Convert the pathlib.Path object to a string for os.environ
    temp_dir = str(tmp_path / "xdg_state")

    # 2. Use monkeypatch to set the environment variable
    #    This ensures it is automatically restored/unset after the test completes.
    monkeypatch.setenv("XDG_STATE_HOME", temp_dir)

    # 3. Optional: Print for debugging (you can remove this)
    print(
        f"\n[Test Setup] Setting XDG_STATE_HOME to: {os.environ.get('XDG_STATE_HOME')}"
    )

    # 4. Return the path, in case the test needs to access the directory directly
    return Path(temp_dir)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_data_dir() -> Path:
    """Path to the sample data directory for tests."""
    return Path(__file__).parent / "fixtures" / "sample_data"


@pytest.fixture
def mock_db_path(temp_dir: Path) -> Path:
    """Create a temporary SQLite database for testing."""
    return temp_dir / "test_nhs.db"


@pytest.fixture
def sample_excel_file() -> Path:
    """Path to a sample Excel file for testing."""
    return Path(__file__).parent / "fixtures" / "sample_data" / "sample.xlsx"


@pytest.fixture
def sample_csv_file() -> Path:
    """Path to a sample CSV file for testing."""
    return Path(__file__).parent / "fixtures" / "sample_data" / "sample.csv"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add unit marker to tests in unit test files
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        # Add integration marker to tests in integration test files
        elif "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
