#!/usr/bin/env python3
"""
NHS Provider Data Parser
Parses Excel files downloaded from NHS and loads them into SQLite database
"""

import os
import sqlite3
from typing import List, Optional
from datetime import datetime
import pandas as pd
import typer

# Configuration
DB_PATH = "./data/nhs_provider_data.db"
DATA_DIR = "./data"


def find_data_start_row(df: pd.DataFrame) -> Optional[int]:
    """
    Find the row where actual data starts by looking for 'Region Code' in column B (index 1).
    Returns the row index or None if not found.
    """
    for idx, row in df.iterrows():
        # Check if column B (index 1) contains 'Region Code'
        if pd.notna(row.iloc[1]) and str(row.iloc[1]).strip() == 'Region Code':
            return idx
    return None


def get_field_mapping():
    """Define the fields we want to extract for each data type"""
    return {
        "New-Periods": {
            "cols": [
                "Region Code",
                "Provider Code",
                "Provider Name",
                "Treatment Function Code",
                "Treatment Function",
                "Number of new RTT clock starts during the month"
            ]
        },
        "Admitted": {
            "cols": [
                "Region Code",
                "Provider Code",
                "Provider Name",
                "Treatment Function Code",
                "Treatment Function",
                "Patients with unknown clock start date",
                "Total number of completed pathways (all)",
                "Total number of completed pathways (with a known clock start)",
                "Average (median) waiting time (in weeks)",
                "95th percentile waiting time (in weeks)",
                "Total 52 plus weeks",
                "Total 78 plus weeks",
                "Total 65 plus weeks"
            ]
        },
        "NonAdmitted": {
            "cols": [
                "Region Code",
                "Provider Code",
                "Provider Name",
                "Treatment Function Code",
                "Treatment Function",
                "Patients with unknown clock start date",
                "Total number of completed pathways (all)",
                "Total number of completed pathways (with a known clock start)",
                "Average (median) waiting time (in weeks)",
                "95th percentile waiting time (in weeks)",
                "Total 52 plus weeks",
                "Total 78 plus weeks",
                "Total 65 plus weeks"
            ]
        },
        "Incomplete": {
            "cols": [
                "Region Code",
                "Provider Code",
                "Provider Name",
                "Treatment Function Code",
                "Treatment Function",
                "Total number of incomplete pathways",
                "Total within 18 weeks",
                "% within 18 weeks",
                "Average (median) waiting time (in weeks)",
                "92nd percentile waiting time (in weeks)"
            ]
        },
        "Incomplete_with_DTA": {
            "cols": [
                "Region Code",
                "Provider Code",
                "Provider Name",
                "Treatment Function Code",
                "Treatment Function",
                "Total number of incomplete pathways with a decision to admit for treatment",
                "% of incomplete pathways with a decision to admit for treatment"
            ]
        }
    }


def clean_column_name(col_name: str) -> str:
    """Clean a single column name to be SQL-safe"""
    if pd.isna(col_name):
        return "unknown_column"

    clean_col = str(col_name).strip()

    # Replace spaces and special characters with underscores
    clean_col = clean_col.replace(' ', '_').replace('(', '').replace(')', '')
    clean_col = clean_col.replace('-', '_').replace('/', '_').replace('\\', '_')
    clean_col = clean_col.replace('%', 'pct').replace('+', 'plus')

    # Handle numbers at the start
    if clean_col and clean_col[0].isdigit():
        clean_col = f"col_{clean_col}"

    # Remove multiple consecutive underscores
    import re
    clean_col = re.sub(r'_+', '_', clean_col)

    # Remove leading/trailing underscores
    clean_col = clean_col.strip('_')

    # Ensure it's not empty
    if not clean_col:
        clean_col = "unknown_column"

    return clean_col


def parse_excel_sheet(file_path: str,
                      sheet_name: str,
                      period: str, data_type: str, ) -> Optional[pd.DataFrame]:
    """
    Parse a specific sheet from an Excel file using field mapping.
    Returns a DataFrame with only the fields we're interested in.
    """
    try:
        # Read the Excel sheet
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

        # Find where the actual data starts
        data_start_row = find_data_start_row(df)
        if data_start_row is None:
            print(f"Could not find data start row in {file_path}, sheet {sheet_name}")
            return None

        # Use the data start row as header
        header_row = df.iloc[data_start_row]
        data_df = df.iloc[data_start_row + 1:].copy()

        # Get the field mapping for this data type
        field_mapping = get_field_mapping()
        if data_type not in field_mapping:
            print(f"No field mapping found for data type: {data_type}")
            return None

        target_columns = field_mapping[data_type]["cols"]

        # Create a mapping from original column names to clean names
        column_mapping = {}
        for i, orig_col in enumerate(header_row):
            if pd.notna(orig_col) and str(orig_col).strip() in target_columns:
                clean_name = clean_column_name(str(orig_col).strip())
                column_mapping[i] = clean_name

        # Select only the columns we want
        selected_columns = list(column_mapping.keys())
        if not selected_columns:
            print(f"No target columns found in {file_path}, sheet {sheet_name}")
            return None

        # Extract the data with only our target columns
        filtered_df = data_df.iloc[:, selected_columns].copy()
        filtered_df.columns = [column_mapping[i] for i in selected_columns]

        # Remove completely empty rows
        filtered_df = filtered_df.dropna(how='all')

        # Add period and data_type information
        period_iso = datetime.strptime(period, "%B %Y").strftime("%Y-%m-01")
        filtered_df['period'] = period_iso
        filtered_df['data_type'] = data_type

        # Ensure we have the key columns
        required_cols = ['Region_Code', 'Provider_Code', 'Provider_Name', 'Treatment_Function_Code',
                         'Treatment_Function']
        missing_cols = [col for col in required_cols if col not in filtered_df.columns]
        if missing_cols:
            print(f"Missing required columns in {file_path}, sheet {sheet_name}: {missing_cols}")
            return None

        print(f"Extracted {len(filtered_df)} rows with {len(filtered_df.columns)} columns from {sheet_name}")
        return filtered_df

    except Exception as e:
        print(f"Error parsing {file_path}, sheet {sheet_name}: {e}")
        return None


def find_matching_file(file_type: str, month_year: str) -> Optional[str]:
    """
    Find the actual filename for a given file type and month/year,
    handling various suffixes like 'revised', numbers, etc.
    """
    # Base pattern to match
    base_pattern = f"{file_type}-{month_year}"

    # List all Excel files in the data directory
    try:
        all_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.xlsx')]
    except FileNotFoundError:
        return None

    # Find files that match our pattern
    matching_files = []
    for filename in all_files:
        if filename.startswith(base_pattern):
            matching_files.append(filename)

    if not matching_files:
        return None

    # If multiple matches, prefer 'revised' suffix, otherwise take the first one
    revised_files = [f for f in matching_files if 'revised' in f.lower()]
    if revised_files:
        return revised_files[0]
    else:
        return matching_files[0]


def get_sheet_mapping(file_type: str) -> List[str]:
    """
    Get the list of sheets to parse for each file type.
    """
    if file_type == "Incomplete-Provider":
        return ["Provider", "Provider with DTA", "IS Provider", "IS Provider with DTA"]
    else:  # Admitted-Provider, NonAdmitted-Provider, New-Periods-Provider
        return ["Provider", "IS Provider"]


def create_database_schema(db_path: str):
    """Create the SQLite database schema with composite primary keys"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables for each data type with all possible columns
    field_mapping = get_field_mapping()

    for data_type, config in field_mapping.items():
        table_name = data_type.lower().replace('-', '_')

        # Base columns that all tables have
        base_columns = [
            "period TEXT NOT NULL CHECK(length(period) = 10)",
            "region_code TEXT",
            "provider_code TEXT NOT NULL",
            "provider_name TEXT",
            "treatment_function_code TEXT NOT NULL",
            "treatment_function TEXT",
            "data_type TEXT NOT NULL",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ]

        # Add data-specific columns
        for col in config["cols"]:
            if col not in ["Region Code", "Provider Code", "Provider Name", "Treatment Function Code",
                           "Treatment Function"]:
                clean_col = clean_column_name(col)
                base_columns.append(f"{clean_col} REAL")

        # Create the table with composite primary key
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(base_columns)},
                PRIMARY KEY (period, provider_code, treatment_function_code, data_type)
            )
        """

        cursor.execute(create_sql)
        print(f"Created table {table_name} with {len(base_columns)} columns and composite primary key")

    conn.commit()
    conn.close()
    print(f"Database schema created at {db_path}")


def add_dynamic_columns(conn: sqlite3.Connection, table_name: str, df: pd.DataFrame):
    """Add dynamic columns to the table based on the DataFrame columns"""
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Add new columns that don't exist
    for col in df.columns:
        if col not in existing_columns and col not in ['period', 'region_code', 'provider_code', 'provider_name',
                                                       'treatment_function_code', 'treatment_function', 'data_type']:
            # Determine column type based on data
            if df[col].dtype in ['int64', 'float64']:
                col_type = 'REAL'
            else:
                col_type = 'TEXT'

            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {col_type}")
                print(f"Added column {col} to {table_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    print(f"Error adding column {col} to {table_name}: {e}")


def load_data_to_database(df: pd.DataFrame, table_name: str, data_type: str, db_path: str):
    """Load DataFrame into SQLite database using INSERT OR REPLACE"""
    # Add data_type column if not already present
    df = df.copy()
    if 'data_type' not in df.columns:
        df['data_type'] = data_type

    conn = sqlite3.connect(db_path)
    return load_data_to_database2(df, table_name, conn)


def load_data_to_database2(df: pd.DataFrame, table_name: str, conn):
    """Load DataFrame into SQLite database using INSERT OR REPLACE"""
    cursor = conn.cursor()

    # Get column names
    columns = list(df.columns)
    placeholders = ', '.join(['?' for _ in columns])
    column_names = ', '.join(columns)

    # Insert data row by row using INSERT OR REPLACE
    for _, row in df.iterrows():
        values = [row[col] for col in columns]
        insert_sql = f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"
        try:
            cursor.execute(insert_sql, values)
        except Exception as e:
            print(f"Error inserting row: {e} query : {insert_sql} values: {values} row: {row}")
            cursor.close()
            raise e

    conn.commit()
    print(f"Loaded {len(df)} rows into {table_name}")

    # finally:
    #     conn.close()


def parse_period_data(period: str, force: bool = False):
    """
    Parse all Excel files for a specific period and load into database.
    """
    print(f"\nParsing data for period: {period}")

    # Handle different period formats
    if len(period.split()) == 2:
        # Format: "March 2024" -> "Mar24"
        period_parts = period.split()
        month = period_parts[0][:3]  # First 3 letters of month
        year = period_parts[1][-2:]  # Last 2 digits of year
        month_year = f"{month}{year}"
    elif len(period) == 5 and period[3:].isdigit():
        # Format: "Mar24" -> "Mar24"
        month_year = period
    else:
        print(f"Invalid period format: {period}. Use 'March 2024' or 'Mar24'")
        return

    # File types to process
    file_types = [
        "Incomplete-Provider",
        "Admitted-Provider",
        "NonAdmitted-Provider",
        "New-Periods-Provider"
    ]

    # Table mapping - maps file type and sheet name to data type
    table_mapping = {
        "Incomplete-Provider": {
            "Provider": "Incomplete",
            "Provider with DTA": "Incomplete_with_DTA",
            "IS Provider": "Incomplete",
            "IS Provider with DTA": "Incomplete_with_DTA"
        },
        "Admitted-Provider": {
            "Provider": "Admitted",
            "IS Provider": "Admitted"
        },
        "NonAdmitted-Provider": {
            "Provider": "NonAdmitted",
            "IS Provider": "NonAdmitted"
        },
        "New-Periods-Provider": {
            "Provider": "New-Periods",
            "IS Provider": "New-Periods"
        }
    }

    # Create database if it doesn't exist
    if not os.path.exists(DB_PATH):
        create_database_schema(DB_PATH)

    # Process each file type
    for file_type in file_types:
        # Try to find the file with various suffixes
        filename = find_matching_file(file_type, month_year)
        if not filename:
            print(f"File not found for {file_type}-{month_year}")
            continue

        file_path = os.path.join(DATA_DIR, filename)

        print(f"Processing: {filename}")

        # Get sheets to parse for this file type
        sheets_to_parse = get_sheet_mapping(file_type)

        # Parse each sheet
        for sheet_name in sheets_to_parse:
            try:
                # Check if sheet exists
                xl_file = pd.ExcelFile(file_path)
                if sheet_name not in xl_file.sheet_names:
                    print(f"Sheet '{sheet_name}' not found in {filename}")
                    continue

                # Determine target data type and table
                data_type = table_mapping[file_type][sheet_name]
                target_table = data_type.lower().replace('-', '_')

                # Parse the sheet with the data type
                df = parse_excel_sheet(file_path, sheet_name, period, data_type)
                if df is None or df.empty:
                    print(f"No data found in {filename}, sheet {sheet_name}")
                    continue

                # Load into database
                load_data_to_database(df, target_table, sheet_name, DB_PATH)

            except Exception as e:
                print(f"Error processing {filename}, sheet {sheet_name}: {e}")


def main(
        period: str = typer.Option(None, help="Specific period to parse (e.g., 'March 2024')"),
        all_periods: bool = typer.Option(False, "--all", help="Parse all available periods"),
        force: bool = typer.Option(False, "--force", "-f", help="Force re-parsing even if data exists")
):
    """Parse NHS Provider Data Excel files into SQLite database"""

    if not period and not all_periods:
        typer.echo("Please specify either --period or --all")
        raise typer.Exit(1)

    if period:
        parse_period_data(period, force)
    elif all_periods:
        # Find all available periods by looking at Excel files
        excel_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.xlsx') and 'Provider' in f]
        periods = set()

        for file in excel_files:
            # Extract period from filename (e.g., "Mar24" from "Incomplete-Provider-Mar24-XLSX-revised.xlsx")
            parts = file.split('-')
            if len(parts) >= 3:
                month_year = parts[2]  # e.g., "Mar24"
                periods.add(month_year)

        print(f"Found {len(periods)} unique periods: {sorted(periods)}")

        for period_code in sorted(periods):
            # Convert period code to full period name
            # This is a simplified conversion - you might want to implement proper mapping
            parse_period_data(period_code, force)


if __name__ == "__main__":
    typer.run(main)
