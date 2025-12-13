# utils and constants for processing rtt wtd full csv data


proj_db_path = "db"

# Primary database file - contains all tables
DB_FILE = "nhs_waiting_lists.db"

# Table organization:
# Staging tables (can be truncated/dropped after QA):
#   - all_rtt_raw: Raw CSV dumps with all columns, minimal cleaning
#
# Production tables:
#   - all_rtt: Cleaned RTT data (grouped by provider)
#   - consolidated: Derived metrics from all_rtt
#   - providers: Provider metadata
#   - outpatients_activity: Outpatient attendance data
#   - v_consolidated: View joining consolidated + providers

# main column names common across all parts
base_col_names = [
    "period",
    "provider",
    "provider_org_name",
    "pathway",
    "rtt_part_description",
    "treatment",
    "treatment_function_name",
]

# numeric summary columns
summary_col_names = ["total", "total_all"]

# columns with unknown start clock dates. i.e. not in waiting lists
unknown_start_clock_cols = [
    "unknown_start",
]

# From April 2021 nhs england collected up to 104 weeks of waiting
# before that it was 52 weeks, and a 52-week and greater bucket
wait_ranges = [f"gt_{n:02}_to_{n + 1:02}_weeks" for n in range(104)]
wait_ranges.append("gt_104_weeks")
wait_ranges.append("gt_52_weeks")


wait_ranges_lt_18 = [f"gt_{n:02}_to_{n + 1:02}_weeks" for n in range(18)]
wait_ranges_gte_18 = [f"gt_{n:02}_to_{n + 1:02}_weeks" for n in range(18, 104)]
wait_ranges_gte_18.append("gt_104_weeks")
wait_ranges_gte_18.append("gt_52_weeks")

# all the columns used to calculate the totals_all value
totals_all_cols = wait_ranges + unknown_start_clock_cols

# all the waiting time bucket columns
wait_cols = wait_ranges + summary_col_names

# all columns. used for integrity checks
all_cols = base_col_names + wait_cols + unknown_start_clock_cols

# all the waiting time bucket columns plus unknown start clock columns
numeric_cols = wait_ranges + unknown_start_clock_cols + summary_col_names

# used for generating the table schema
base_columns = [
    # "period TEXT NOT NULL CHECK(length(period) = 10)",
    "period TEXT NOT NULL",
    "provider TEXT NOT NULL",
    "provider_org_name TEXT NOT NULL",
    "pathway TEXT NOT NULL",
    "rtt_part_description TEXT NOT NULL",
    "treatment TEXT NOT NULL",
    "treatment_function_name TEXT NOT NULL",
]

rtt_base_columns = [
    # "period TEXT NOT NULL CHECK(length(period) = 10)",
    "period TEXT NOT NULL",
    "provider TEXT NOT NULL",
    "pathway TEXT NOT NULL",
    "treatment TEXT NOT NULL",
]

# cols used to aggregate providers who operate under multiple commissioning orgs
group_cols = ["period", "provider", "pathway", "treatment"]

# to extract the month from a period string
MONTHS = {
    "APRIL": 4,
    "MAY": 5,
    "JUNE": 6,
    "JULY": 7,
    "AUGUST": 8,
    "SEPTEMBER": 9,
    "OCTOBER": 10,
    "NOVEMBER": 11,
    "DECEMBER": 12,
    "JANUARY": 1,
    "FEBRUARY": 2,
    "MARCH": 3,
}


# Month abbreviation to number mapping
MONTH_MAP = {
    "Jan": "01",
    "Feb": "02",
    "Mar": "03",
    "Apr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Aug": "08",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dec": "12",
}

# 1. Map RTT part names to readable categories
map_names = {
    "Part_1A": "admitted",
    "Part_1B": "nonadmitted",
    "Part_2": "incomplete",
    "Part_2A": "incomplete_dta",
    "Part_3": "new_periods",
}


LARGE_ACUTE_PROVIDER_CODES = [
    "R0B",
    "RAJ",
    "RDE",
    "RDU",
    "REF",
    "RGN",
    "RH8",
    "RHU",
    "RHW",
    "RJ2",
    "RL4",
    "RN5",
    "RTE",
    "RTF",
    "RVJ",
    "RWD",
    "RWF",
    "RWH",
    "RWP",
    "RWY",
    "RXC",
    "RXK",
    "RXR",
]


OTHER_ACUTE_PROVIDER_CODES = [
    "R0B",
    "RDE",
    "RDU",
    "REF",
    "RGN",
    "RH8",
    "RHU",
    "RHW",
    "RJ2",
    "RL4",
    "RN5",
    "RTE",
    "RTF",
    "RVJ",
    "RWD",
    "RWF",
    "RWH",
    "RWP",
    "RWY",
    "RXC",
    "RXK",
    "RXR",
]


NO_OUTLIERS_ACUTE_PROVIDER_CODES = [
    "R0B",
    # "RAJ",
    "RDE",
    "RDU",
    "REF",
    "RGN",
    "RH8",
    "RHU",
    # "RHW",
    "RJ2",
    "RL4",
    "RN5",
    # "RTE",
    "RTF",
    "RVJ",
    "RWD",
    "RWF",
    "RWH",
    "RWP",
    "RWY",
    "RXC",
    "RXK",
    "RXR",
]

ALL_PROVIDER_CODES = [
    "R0A",
    "R0B",
    "R0D",
    "R1F",
    "R1H",
    "R1K",
    "RA2",
    "RA7",
    "RA9",
    "RAE",
    "RAJ",
    "RAL",
    "RAN",
    "RAS",
    "RAX",
    "RBD",
    "RBK",
    "RBL",
    "RBN",
    "RBQ",
    "RBS",
    "RBT",
    "RBV",
    "RC9",
    "RCB",
    "RCD",
    "RCF",
    "RCU",
    "RCX",
    "RD1",
    "RD8",
    "RDE",
    "RDU",
    "REF",
    "REM",
    "REN",
    "REP",
    "RET",
    "RF4",
    "RFF",
    "RFR",
    "RFS",
    "RGM",
    "RGN",
    "RGP",
    "RGR",
    "RGT",
    "RH5",
    "RH8",
    "RHM",
    "RHQ",
    "RHU",
    "RHW",
    "RJ1",
    "RJ2",
    "RJ6",
    "RJ7",
    "RJC",
    "RJE",
    "RJL",
    "RJN",
    "RJR",
    "RJZ",
    "RK5",
    "RK9",
    "RKB",
    "RKE",
    "RL1",
    "RL4",
    "RLQ",
    "RLT",
    "RM1",
    "RM3",
    "RMC",
    "RMP",
    "RN3",
    "RN5",
    "RN7",
    "RNA",
    "RNN",
    "RNQ",
    "RNS",
    "RNZ",
    "RP4",
    "RP5",
    "RP6",
    "RPA",
    "RPC",
    "RPY",
    "RQ3",
    "RQM",
    "RQW",
    "RQX",
    "RR7",
    "RR8",
    "RRF",
    "RRJ",
    "RRK",
    "RRV",
    "RTD",
    "RTE",
    "RTF",
    "RTG",
    "RTH",
    "RTK",
    "RTP",
    "RTR",
    "RTX",
    "RVJ",
    "RVR",
    "RVV",
    "RVW",
    "RWA",
    "RWD",
    "RWE",
    "RWF",
    "RWG",
    "RWH",
    "RWJ",
    "RWP",
    "RWW",
    "RWY",
    "RX1",
    "RXC",
    "RXF",
    "RXK",
    "RXL",
    "RXN",
    "RXP",
    "RXQ",
    "RXR",
    "RXW",
    "RYJ",
    "RYR",
]

TREATMENT_CODES = (
    "C_101",
    "C_110",
    "C_320",
    "C_330",
    "C_400",
    "C_502",
    "C_301",
    "C_999",
)


ALL_TREATMENT_CODES = (
    "C_100",
    "C_101",
    "C_110",
    "C_120",
    "C_130",
    "C_140",
    "C_150",
    "C_160",
    "C_170",
    "C_300",
    "C_301",
    "C_320",
    "C_330",
    "C_340",
    "C_400",
    "C_410",
    "C_430",
    "C_502",
    "X02",
    "X03",
    "X04",
    "X05",
    "X06",
)

TOTAL_ONLY_TREATMENT_CODES = ("C_999",)

# PROVIDER_CODES = ['R0B', 'RAJ', 'RTH', 'RTE', "RTF", "RWF", "RTE", "REF",
# "RWH", "R0B", "RVJ", "RHW", "RDU", "RH8",
#                   "RWY",
#                   "RXC", "RL4", "RDE", "RXK", "RXR", "RJ2", "RN5", "RHU",
#                   "RGN", "RWP", "RWD", "RAJ", 'RTF', 'RXC']
# # PROVIDER_COEDS = ('RAJ', 'RTH', 'RJZ', 'RH5', 'R0B', 'RTF', 'RXC')


# large departments
# TREATMENT_CODES = (
#     'C_100',
#     'C_101',
#     'C_110',
#     'C_320',
#     'C_330',
#     'C_400',
#     'C_502',
#     'C_301'
# )
