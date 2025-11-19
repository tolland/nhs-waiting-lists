from datetime import date
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta

from nhs_waiting_lists.utils.csv_format_spec import RTTFormatRegistry


def last_full_quarter(latest_period: str):
    """
    Given latest_period = 'YYYY-MM', return (year, quarter)
    for the *last complete quarter*.
    """
    year, month = map(int, latest_period.split('-'))
    delta = month % 3
    d = date(year, month, 1) - relativedelta(months=delta)  # step back 1 month
    q = ((d.month - 1) // 3) + 1
    return d.year, q

def two_years_to_nhs_year(two_years: str|int) -> str:
    """
    Convert a 4-digit string containing the last two digits of this and next financial year
    into 'YYYY-YY' format.
    Examples:
      '2425' -> '2024-25'
      '9899' -> '1998-99'
    Uses a 50-year pivot: 00-49 -> 2000-2049, 50-99 -> 1950-1999.
    """
    if isinstance(two_years, int):
        two_years = str(two_years)
    s = two_years.strip()
    if len(s) != 4 or not s.isdigit():
        raise ValueError(f"expected 4 digit string like '2425' or '9899' got '{two_years}' '{type(two_years)}'")
    a, b = int(s[:2]), int(s[2:])
    if b != (a + 1) % 100:
        raise ValueError("invalid consecutive years; expected next-year pair")
    century = 1900 if a >= 50 else 2000
    start_year = century + a
    return f"{start_year}-{str(b).zfill(2)}"

def last_n_full_quarters(latest_period: str, n=3):
    year, q = last_full_quarter(latest_period)
    quarters = []
    for _ in range(n):
        quarters.append((year, q))
        q -= 1
        if q == 0:
            q = 4
            year -= 1
    return list(reversed(quarters))

def period_to_nhs_year(period: str) -> str:
    """
    Convert period 'yyyy-mm' to NHS year '2023-24'
    @note: they also variously use ambiguous shorter version like '2324' in older data
    """
    year, month = map(int, period.split('-'))
    print(f"year: {year}, month: {month}")
    if month >= 4:
        return f"{str(year)[0:4]}-{str(year+1)[2:4]}"
    else:
        return f"{str(year - 1)[0:4]}-{str(year)[2:4]}"

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

import re
import pandas as pd

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
