from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Set

import pandas as pd

from src.nhs_rtt.utils.utils2 import CSVFormatSpec, load_rtt_csv


@dataclass
class FormatValidator:
    """Validates CSV format matches expectations."""

    expected_columns: Set[str]
    required_columns: Set[str]

    def validate(self, df: pd.DataFrame, filepath: Path) -> list[str]:
        """Validate dataframe structure, return list of issues."""
        issues = []

        actual_cols = set(df.columns)
        missing_required = self.required_columns - actual_cols
        if missing_required:
            issues.append(f"Missing required columns: {missing_required}")

        unexpected = actual_cols - self.expected_columns
        if unexpected:
            issues.append(f"Unexpected columns: {unexpected}")

        return issues


class RTTFormatRegistry:
    # ... existing code ...

    def __init__(self):
        self.formats: list[tuple[date, date, CSVFormatSpec]] = []
        self.validator = FormatValidator(
            expected_columns={
                "Period",
                "Provider Parent Org Code",
                "Provider Parent Name",
                "Provider Org Code",
                "Provider Org Name",
                "RTT Part Type",
                "Treatment Function Code",
                # ... add all expected columns
            },
            required_columns={"Period", "Provider Org Code", "Treatment Function Code"},
        )
        self._setup_default_formats()

    def load_and_validate(
        self, filepath: Path, period_date: date
    ) -> tuple[pd.DataFrame, list[str]]:
        """Load CSV and validate format."""
        df = load_rtt_csv(filepath, period_date, self)
        issues = self.validator.validate(df, filepath)

        if issues:
            print(f"Format issues in {filepath}:")
            for issue in issues:
                print(f"  - {issue}")

        return df, issues
