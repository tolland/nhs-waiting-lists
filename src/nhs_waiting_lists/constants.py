import sys
import numpy as np
# utils and constants for processing rtt wtd full csv data


proj_db_path = "db"

# main column names common across all parts
base_col_names = [
    'period',
    'provider_org_code',
    'provider_org_name',
    'rtt_part_type',
    'rtt_part_description',
    'treatment_function_code',
    'treatment_function_name'
]

# numeric summary columns
summary_col_names = [
    'total',
    'total_all'
]

# columns with unknown start clock dates. i.e. not in waiting lists
unknown_start_clock_cols = [
    'patients_with_unknown_clock_start_date',
]

# From April 2021 nhs england collected up to 104 weeks of waiting
# before that it was 52 weeks, and a 52-week and greater bucket
wait_ranges = [f"gt_{n:02}_to_{n + 1:02}_weeks" for n in range(104)]
wait_ranges.append("gt_104_weeks")


wait_ranges_lt_18 = [f"gt_{n:02}_to_{n + 1:02}_weeks" for n in range(18)]
wait_ranges_gte_18 = [f"gt_{n:02}_to_{n + 1:02}_weeks" for n in range(18,104)]
wait_ranges_gte_18.append("gt_104_weeks")

# all the columns used to calculate the totals_all value
totals_all_cols = wait_ranges + unknown_start_clock_cols

# all the waiting time bucket columns
wait_cols = wait_ranges + summary_col_names

# all columns. used for integrity checks
all_cols = base_col_names + wait_cols + unknown_start_clock_cols

# all the waiting time bucket columns plus unknown start clock columns
numeric_cols =  wait_ranges + unknown_start_clock_cols + summary_col_names

# used for generating the table schema
base_columns = [
    # "period TEXT NOT NULL CHECK(length(period) = 10)",
    "period TEXT NOT NULL",
    "provider_org_code TEXT NOT NULL",
    "provider_org_name TEXT NOT NULL",
    "rtt_part_type TEXT NOT NULL",
    "rtt_part_description TEXT NOT NULL",
    "treatment_function_code TEXT NOT NULL",
    "treatment_function_name TEXT NOT NULL",
]

rtt_base_columns = [
    # "period TEXT NOT NULL CHECK(length(period) = 10)",
    "period TEXT NOT NULL",
    "provider_org_code TEXT NOT NULL",
    "rtt_part_type TEXT NOT NULL",
    "treatment_function_code TEXT NOT NULL",
]

# cols used to aggregate providers who operate under multiple commissioning orgs
group_cols = [
    'period',
    'provider_org_code',
    'rtt_part_type',
    'treatment_function_code'
]

# to extract the month from a period string
MONTHS = {
    "APRIL": 4, "MAY": 5, "JUNE": 6, "JULY": 7,
    "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10,
    "NOVEMBER": 11, "DECEMBER": 12,
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3,
}


# Month abbreviation to number mapping
MONTH_MAP = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
}

# 1. Map RTT part names to readable categories
map_names = {
    "Part_1A": "admitted",
    "Part_1B": "nonadmitted",
    "Part_2": "incomplete",
    "Part_2A": "incomplete_dta",
    "Part_3": "new_period",
}

PROVIDER_CODES = ['R0B', 'RAJ', 'RTH', 'RTE', "RTF", "RWF", "RTE", "REF", "RWH", "R0B", "RVJ", "RHW",
                  "RDU", "RH8", "RWY", "RXC", "RL4", "RDE", "RXK", "RXR", "RJ2", "RN5", "RHU",
                  "RGN", "RWP", "RWD", "RAJ"]
TREATMENT_CODES = ('C_101', 'C_110', 'C_320', 'C_330', 'C_400', 'C_502', 'C_301', 'C_999')