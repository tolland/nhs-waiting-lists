"""
Pytest configuration and shared fixtures for NHS waiting lists package tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Generator


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_data_dir() -> Path:
    """Path to sample data directory for tests."""
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
