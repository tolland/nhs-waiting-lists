import sqlite3

import pandas as pd


def get_sqlite_max_variables() -> int:
    """
    Detect SQLITE_MAX_VARIABLE_NUMBER for the current SQLite version.

    Returns 999 for old SQLite or 32766 for SQLite 3.32.0+
    """
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    # Try to get the limit by attempting a query with known parameters
    # SQLite default is 999 for old versions, 32766 for 3.32.0+
    try:
        # Check SQLite version
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        major, minor, patch = map(int, version.split("."))

        # SQLite 3.32.0+ has higher limit
        if (major, minor, patch) >= (3, 32, 0):
            return 32766
        else:
            return 999
    finally:
        conn.close()


def calculate_optimal_chunksize(num_columns: int, safety_factor: float = 0.9) -> int:
    """
    Calculate optimal chunksize for pandas to_sql with method='multi'.

    Args:
        num_columns: Number of columns in the DataFrame
        safety_factor: Safety margin (default 0.9 = 90% of limit)

    Returns:
        Optimal chunksize that won't exceed SQLITE_MAX_VARIABLE_NUMBER
    """
    max_vars = get_sqlite_max_variables()
    # Calculate: chunksize = max_vars / num_columns, with safety factor
    optimal = int((max_vars / num_columns) * safety_factor)
    # Ensure at least 1 row per chunk
    return max(1, optimal)



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
