#!/usr/bin/env python3

import pandas as pd

"""
NHS Provider Data Parser
Parses Excel files downloaded from NHS and loads them into SQLite database
"""

# Configuration
DB_PATH = "./data/nhs_provider_data.db"
DATA_DIR = "./data"

FIELD_MAPPING = {
    "acute-providers": {
        "sheets": {
            "name": "Provider Table",
            "cols": [
                "Trust Code",
                "Trust Name",
                {
                    "prefix": "Percentage waiting within 18 weeks for elective treatment",
                    "name": "pct_18wks_elective",
                }
            ]
        },
    }
}

df = pd.read_excel(
    './data/acute-provider-table-oct-25-publication-data.xlsx',
    sheet_name="Provider table",
    usecols="B:J",
    skiprows=9,
    skipfooter=5
)

print(df)
