from datetime import date
from datetime import datetime
from typing import List

import pandas as pd
from dateutil.relativedelta import relativedelta

from nhs_waiting_lists.constants import (
    MONTHS,
)


def parse_rtt_period(value: str) -> str:
    _, month_str, year_str = value.split("-")
    month = MONTHS[month_str.upper()]
    return f"{int(year_str):04d}-{month:02d}"


def fiscal_to_calendar(row: pd.Series) -> str:
    """
    Convert fiscal year + period name to calendar period (YYYY-MM).

    Fiscal year format: "2016-17" (April of first year to March of second)
    Period name: Capitalized month name (e.g., "JUNE")

    Returns period in "YYYY-MM" format.
    """
    start_year, end_year = row["Year"].split("-")
    month = MONTHS[row["Period Name"].upper()]
    # April–December belong to start_year, Jan–Mar to end_year
    year = int(start_year) if month >= 4 else int(start_year) + 1
    return f"{year:04d}-{month:02d}"

def fix_rtt_period(row: pd.Series) -> str:
    """
    This is a work around for the inconsistent period format in RTT data.
    @TODO this needs to be handled more obviously
    :param row:
    :return:
    """
    if row["Period"].startswith("RTT-"):
        return parse_rtt_period(row["Period"])
    else:
        start_yyyy, end_yy, month = row["Period"].split("-")
        year = int(start_yyyy) if MONTHS[month] >= 4 else (int(start_yyyy) + 1)
        return f"{year:04d}-{MONTHS[month]:02d}"


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

def previous_period(period: str) -> str:
    dt = datetime.strptime(period, "%Y-%m")
    prev = dt - relativedelta(months=1)
    return prev.strftime("%Y-%m")

def generate_periods(start: str, end: str | None) -> List[str]:
    """
    Generate inclusive list of periods in YYYY-MM format.

    Args:
        start: Start period in YYYY-MM format
        end: End period in YYYY-MM format, or None to use only start period

    Returns:
        List of periods in YYYY-MM format, in chronological order

    Raises:
        ValueError: If periods are invalid or end is before start
    """
    try:
        start_date = datetime.strptime(start, "%Y-%m")
    except ValueError as e:
        raise ValueError(f"Invalid start period '{start}': {e}")

    if end is None:
        return [start]

    try:
        end_date = datetime.strptime(end, "%Y-%m")
    except ValueError as e:
        raise ValueError(f"Invalid end period '{end}': {e}")

    if end_date < start_date:
        raise ValueError(f"End period '{end}' cannot be before start period '{start}'")

    periods: list[str] = []
    current = start_date
    while current <= end_date:
        periods.append(current.strftime("%Y-%m"))
        current += relativedelta(months=1)

    return periods
