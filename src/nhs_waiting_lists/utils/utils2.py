from datetime import date
from pathlib import Path
import re
import pandas as pd
from dateutil.relativedelta import relativedelta

from nhs_waiting_lists.utils.csv_format_spec import RTTFormatRegistry


def load_rtt_csv(
        filepath: Path,
        period_date: date,
        registry: RTTFormatRegistry
) -> pd.DataFrame:
    """Load RTT CSV with appropriate format specification."""
    spec = registry.get_spec(period_date)

    df = pd.read_csv(filepath, **spec.to_read_csv_kwargs())

    # Apply column mapping if specified
    if spec.column_mapping:
        df = df.rename(columns=spec.column_mapping)

    # Strip whitespace from column names (common issue)
    df.columns = df.columns.str.strip()

    return df

def normalize_measure(value: str) -> str:
    """
    Normalise historic measure names like '01.Attended first appointment'
    to the canonical 'Attended first appointment'.

    - Strips leading numeric prefixes like '01.', '10.', etc.
    - Trims whitespace and quotes
    - Returns unchanged if already normalised
    - Raises if the pattern looks unfamiliar
    """
    if pd.isna(value):
        return value

    # Trim whitespace and quotes
    val = str(value).strip().strip('"')

    # Strip numeric prefix if present
    cleaned = re.sub(r'^\d+\.', '', val).strip()

    # Sanity-check: cleaned must still be in the expected set
    EXPECTED = {
        #
        "Attended first appointment",
        "Attended first tele consultation",
        "Attended subsequent appointment",
        "Attended subsequent tele consultation",
        "Attended but first/subsequent/tele unknown",
        "Did not attend first appointment",
        "Did not attend first tele consultation",
        "Did not attend subsequent appointment",
        "Did not attend subsequent tele consultation",
        "Did not attend, first/ subsequent/ tele unknown",
        "Patient cancelled first appointment",
        "Patient cancelled first tele consultation",
        "Patient cancelled subsequent appointment",
        "Patient cancelled subsequent tele consultation",
        "Patient cancelled appointment, first/ subsequent/ tele unknown",
        "Hospital postponed/ cancelled first appointment",
        "Hospital postponed/ cancelled first tele consultation",
        "Hospital postponed/ cancelled subsequent appointment",
        "Hospital postponed/ cancelled subsequent tele consultation",
        "Hospital postponed/ cancelled appointment, first/ subsequent/ tele unknown",
        "Unknown",
        "Attended-Female",
        "Attended-Male",
        "Attended-Unknown Gender",
        "DNA-Female",
        "DNA-Male",
        "DNA-Unknown Gender",
        "Patient Cancelled-Female",
        "Patient Cancelled-Male",
        "Patient Cancelled-Unknown Gender",
        "Hospital Cancelled-Female",
        "Hospital Cancelled-Male",
        "Hospital Cancelled-Unknown Gender",
        "Unknown Outcome-Female",
        "Unknown Outcome-Male",
        "Unknown Outcome-Unknown Gender",
        "Cardiology",
        "Clinical Haematology",
        "Dermatology",
        "Ear, Nose & Throat (ENT)",
        "Gynaecology",
        "Obstetrics",
        "Ophthalmology",
        "Paediatrics",
        "Rheumatology",
        "Trauma & Orthopaedics",
        # by-age
        "00-09",
        "10-19",
        "20-29",
        "30-39",
        "40-49",
        "50-59",
        "60-69",
        "70-79",
        "80-89",
        "90+",
        "Unknown",
        "Same Day",
        "Under 1 Month",
        "1-2 Months",
        "2-3 Months",
        "3-6 Months",
        "6-9 Months",
        "9-12 Months",
        "12-18 Months",
        "18+ Months",
        "Unknown",
        "Mean",
        "Median",
        #
        "Another appointment given",
        "Appointment to be made at later date",
        "Discharged from consultants care (last attendance)",
        "Unknown",
        #
        "From a consultant, other than in an A&E department",
        "General medical practitioner",
        "Other",
        "Referred from A&E department",
    }

    if cleaned not in EXPECTED:
        raise ValueError(f"Unexpected measure name: {value!r}")

    return cleaned
