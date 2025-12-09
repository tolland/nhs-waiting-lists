
import sqlite3



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


"""
NHS RTT Data Importer
Imports RTT waiting times data downloaded from NHS into SQLite database

Import stages:
1. Raw import: CSV → all_rtt_raw table (staging, all columns)
2. QA checks: Verify totals, check for discrepancies
3. Aggregation: all_rtt_raw → all_rtt (group by provider, drop commissioner cols)
4. Consolidation: all_rtt → consolidated (pivot + lag + derived metrics)
"""
