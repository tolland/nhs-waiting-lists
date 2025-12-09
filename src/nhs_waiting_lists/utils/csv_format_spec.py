import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional, Dict, Any, List


@dataclass
class CSVFormatSpec:
    """Specification for parsing CSV files with varying formats."""

    skiprows: Optional[int] = None
    encoding: str = "utf-8"
    header: int = 0
    column_mapping: Optional[Dict[str, str]] = None  # Old name -> new name
    column_concat: Optional[Dict[str, List[str]]] = None
    cols_to_drop: Optional[List[str]] = None
    date_format: Optional[str] = None
    # New: identifier for format detection
    format_name: str = "default"

    def to_read_csv_kwargs(self) -> Dict[str, Any]:
        """Convert to pandas read_csv kwargs."""
        kwargs = {
            "encoding": self.encoding,
            "header": self.header,
        }
        if self.skiprows is not None:
            kwargs["skiprows"] = self.skiprows
        return kwargs


class RTTFormatRegistry:
    """Registry of format specifications for RTT CSV files."""

    def __init__(self):
        self.formats: list[tuple[date, date, CSVFormatSpec]] = []
        self._setup_default_formats()

    def _setup_default_formats(self):
        """Define the known format changes."""
        # early files with frontmatter and weird column names
        self.register(
            start=date(2000, 4, 1),  # Adjust based on earliest data
            end=date(2016, 6, 30),
            spec=CSVFormatSpec(
                skiprows=2,  # Skip the frontmatter lines
                column_mapping={
                    "RTT Part Name": "pathway",
                },
                column_concat={"Period": ["Year", "Period Name"]},
                format_name="pre_july_2016",
            ),
        )
        self.register(
            start=date(2016, 7, 1),  # Adjust based on earliest data
            end=date(2016, 7, 31),
            spec=CSVFormatSpec(
                skiprows=2,  # Skip the frontmatter lines
                column_mapping={
                    "Treatment Function Name": "treatment",
                    "Treatment Function Description": "Treatment Function Name",
                    "RTT Part Name": "pathway",
                },
                column_concat={"Period": ["Year", "Period Name"]},
                format_name="july_2016",
            ),
        )
        self.register(
            start=date(2016, 8, 1),  # Adjust based on earliest data
            end=date(2017, 9, 30),
            spec=CSVFormatSpec(
                skiprows=2,  # Skip the frontmatter lines
                column_mapping={
                    "RTT Part Name": "pathway",
                },
                column_concat={"Period": ["Year", "Period Name"]},
                format_name="pre_oct_2017",
            ),
        )

        # October 2017 onwards: clean format, assumed ongoing
        self.register(
            start=date(2017, 10, 1),
            end=date(2099, 12, 31),  # Open-ended
            spec=CSVFormatSpec(
                format_name="post_oct_2017",
                column_mapping={
                    "Treatment Function Code": "treatment",
                    "RTT Part Type": "pathway",
                    "Provider Org Code": "provider",
                    "Provider Parent Org Code": "provider_parent",
                    "Commissioner Parent Org Code": "commissioner_parent",
                    "Commissioner Org Code": "commissioner",
                    "Patients with unknown clock start date": "unknown_start",
                },
                cols_to_drop=[
                    "Provider Parent Name",
                    "Provider Org Name",
                    "Commissioner Parent Name",
                    "Commissioner Org Name",
                    "RTT Part Description",
                    "Treatment Function Name",
                ],
            ),
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

    def detect_format(self, filepath: Path) -> CSVFormatSpec:
        """
        Detect CSV format by peeking at file headers.

        Returns the appropriate CSVFormatSpec based on file structure.
        Handles both plain CSV and zipped CSV files.
        """
        # Handle zipped files
        if filepath.suffix == ".zip":
            with zipfile.ZipFile(filepath, "r") as zf:
                # Assume first CSV in zip is the data file
                csv_files = [name for name in zf.namelist() if name.endswith(".csv")]
                if not csv_files:
                    raise ValueError(f"No CSV file found in {filepath}")

                with zf.open(csv_files[0]) as f:
                    # Read first few lines to detect format
                    first_lines = [f.readline().decode("utf-8") for _ in range(5)]
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                first_lines = [f.readline() for _ in range(5)]

        # Detect frontmatter (pre-Oct 2017)
        # These files have non-CSV content at the top
        first_line = first_lines[0].strip()
        if not first_line.startswith('"') and "," not in first_line[:50]:
            # Likely has frontmatter
            for i, line in enumerate(first_lines):
                if "Period" in line or "Provider" in line:
                    # Found header row
                    return CSVFormatSpec(
                        skiprows=i,
                        column_mapping={
                            "Period Name": "Period",
                            "RTT Part Name": "RTT Part Type",
                        },
                        format_name="detected_frontmatter",
                    )

        # Check header columns to distinguish formats
        header_line = first_lines[0] if "," in first_lines[0] else first_lines[3]

        if "Period Name" in header_line or "RTT Part Name" in header_line:
            # Old format with different column names
            return CSVFormatSpec(
                column_mapping={
                    "Period Name": "Period",
                    "RTT Part Name": "RTT Part Type",
                },
                format_name="detected_old_names",
            )

        # Default modern format
        return CSVFormatSpec(format_name="detected_modern")

    def get_spec_with_fallback(
        self, filepath: Path, period_date: Optional[date] = None
    ) -> CSVFormatSpec:
        """
        Get format spec, trying period-based lookup first, then file detection.

        Args:
            filepath: Path to CSV (may be zipped)
            period_date: Optional date to try registry lookup first

        Returns:
            CSVFormatSpec for this file
        """
        # Try date-based lookup first if date provided
        if period_date:
            try:
                spec = self.get_spec(period_date)
                return spec
            except ValueError:
                pass  # Fall through to detection

        # Fall back to file detection
        return self.detect_format(filepath)
