from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict, Any
from pathlib import Path
import pandas as pd

from datetime import date
from dateutil.relativedelta import relativedelta

@dataclass
class CSVFormatSpec:
    """Specification for parsing CSV files with varying formats."""
    skiprows: Optional[int] = None
    encoding: str = 'utf-8'
    header: int = 0
    column_mapping: Optional[Dict[str, str]] = None  # Old name -> new name
    date_format: Optional[str] = None

    def to_read_csv_kwargs(self) -> Dict[str, Any]:
        """Convert to pandas read_csv kwargs."""
        kwargs = {
            'encoding': self.encoding,
            'header': self.header,
        }
        if self.skiprows is not None:
            kwargs['skiprows'] = self.skiprows
        return kwargs


class RTTFormatRegistry:
    """Registry of format specifications for RTT CSV files."""

    def __init__(self):
        self.formats: list[tuple[date, date, CSVFormatSpec]] = []
        self._setup_default_formats()

    def _setup_default_formats(self):
        """Define the known format changes."""
        # Pre-October 2017: files with frontmatter
        self.register(
            start=date(2015, 4, 1),  # Adjust based on earliest data
            end=date(2017, 9, 30),
            spec=CSVFormatSpec(
                skiprows=3,  # Skip the frontmatter lines
                column_mapping={
                    'Period Name': 'Period',
                    'RTT Part Name': 'RTT Part Type',
                }
            )
        )

        # October 2017 onwards: clean format
        self.register(
            start=date(2017, 10, 1),
            end=date(2099, 12, 31),  # Open-ended
            spec=CSVFormatSpec()
        )

    def register(self, start: date, end: date, spec: CSVFormatSpec):
        """Register a format specification for a date range."""
        self.formats.append((start, end, spec))
        # Keep sorted by start date
        self.formats.sort(key=lambda x: x[0])

    def get_spec(self, period_date: date) -> CSVFormatSpec:
        """Get the format spec for a given period date."""
        for start, end, spec in self.formats:
            if start <= period_date <= end:
                return spec
        raise ValueError(f"No format specification found for date {period_date}")