#!/usr/bin/env python3
"""
Create a consolidated NHS database with normalized tables and synthetic columns.

This script creates a new database with:
- metrics table: consolidated data with synthetic previous period columns
- providers table: normalized provider information
- treatments table: normalized treatment function information
"""

import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Tuple


def create_consolidated_database(source_db_path: str, target_db_path: str) -> None:
    """Create the consolidated database with normalized tables."""
    
    # Remove existing target database if it exists
    if os.path.exists(target_db_path):
        os.remove(target_db_path)
    
    # Connect to source and target databases
    source_conn = sqlite3.connect(source_db_path)
    target_conn = sqlite3.connect(target_db_path)
    
    try:
        # Create the normalized tables
        create_providers_table(target_conn)
        create_treatments_table(target_conn, source_conn)
        create_metrics_table(target_conn)
        
        # Populate the tables
        populate_providers_table(target_conn, source_conn)
        populate_treatments_table(target_conn, source_conn)
        populate_metrics_table(target_conn, source_conn)
        
        # Create indexes for better performance
        create_indexes(target_conn)
        
        target_conn.commit()
        print(f"Successfully created consolidated database at {target_db_path}")
        
    finally:
        source_conn.close()
        target_conn.close()


def create_providers_table(conn: sqlite3.Connection) -> None:
    """Create the providers table."""
    conn.execute("""
        CREATE TABLE providers (
            provider_code TEXT PRIMARY KEY,
            provider_name TEXT NOT NULL,
            region_code TEXT
        )
    """)


def create_treatments_table(conn: sqlite3.Connection, source_conn: sqlite3.Connection) -> None:
    """Create the treatments table."""
    conn.execute("""
        CREATE TABLE treatments (
            treatment_function_code TEXT PRIMARY KEY,
            treatment_function_name TEXT NOT NULL
        )
    """)


def create_metrics_table(conn: sqlite3.Connection) -> None:
    """Create the metrics table with synthetic columns."""
    conn.execute("""
        CREATE TABLE metrics (
            period TEXT NOT NULL,
            provider_code TEXT NOT NULL,
            treatment_function_code TEXT NOT NULL,
            
            -- Core metrics
            incomplete REAL,
            admitted REAL,
            new_periods REAL,
            nonadmitted REAL,
            
            -- Synthetic previous period columns
            incomplete_prev REAL,
            admitted_prev REAL,
            new_periods_prev REAL,
            nonadmitted_prev REAL,
            
            PRIMARY KEY (period, provider_code, treatment_function_code),
            FOREIGN KEY (provider_code) REFERENCES providers(provider_code),
            FOREIGN KEY (treatment_function_code) REFERENCES treatments(treatment_function_code)
        )
    """)


def populate_providers_table(conn: sqlite3.Connection, source_conn: sqlite3.Connection) -> None:
    """Populate the providers table with unique provider information."""
    # Get data from source database - use the most common region_code for each provider
    cursor = source_conn.cursor()
    cursor.execute("""
        SELECT 
            provider_code,
            provider_name,
            region_code
        FROM (
            SELECT 
                provider_code,
                provider_name,
                region_code,
                COUNT(*) as region_count,
                ROW_NUMBER() OVER (
                    PARTITION BY provider_code 
                    ORDER BY COUNT(*) DESC, region_code
                ) as rn
            FROM incomplete
            WHERE provider_code IS NOT NULL 
              AND provider_name IS NOT NULL
              AND region_code IS NOT NULL
            GROUP BY provider_code, provider_name, region_code
        ) ranked
        WHERE rn = 1
        ORDER BY provider_code
    """)
    
    # Insert into target database
    target_cursor = conn.cursor()
    target_cursor.executemany("""
        INSERT INTO providers (provider_code, provider_name, region_code)
        VALUES (?, ?, ?)
    """, cursor.fetchall())
    print("Populated providers table")


def populate_treatments_table(conn: sqlite3.Connection, source_conn: sqlite3.Connection) -> None:
    """Populate the treatments table with the most recent treatment function names."""
    # Get the most recent treatment function name for each code
    # This handles cases where names change over time (e.g., "Cardiology" -> "Cardiology Service")
    cursor = source_conn.cursor()
    cursor.execute("""
        SELECT 
            treatment_function_code,
            treatment_function
        FROM (
            SELECT 
                treatment_function_code,
                treatment_function,
                ROW_NUMBER() OVER (
                    PARTITION BY treatment_function_code 
                    ORDER BY period DESC
                ) as rn
            FROM incomplete
            WHERE treatment_function_code IS NOT NULL 
              AND treatment_function IS NOT NULL
        ) ranked
        WHERE rn = 1
        ORDER BY treatment_function_code
    """)
    
    # Insert into target database
    target_cursor = conn.cursor()
    target_cursor.executemany("""
        INSERT INTO treatments (treatment_function_code, treatment_function_name)
        VALUES (?, ?)
    """, cursor.fetchall())
    print("Populated treatments table")


def populate_metrics_table(conn: sqlite3.Connection, source_conn: sqlite3.Connection) -> None:
    """Populate the metrics table with consolidated data and synthetic columns."""
    
    # First, get all unique combinations of period, provider_code, treatment_function_code
    source_cursor = source_conn.cursor()
    source_cursor.execute("""
        SELECT DISTINCT period, provider_code, treatment_function_code
        FROM (
            SELECT period, provider_code, treatment_function_code FROM incomplete
            UNION
            SELECT period, provider_code, treatment_function_code FROM admitted
            UNION
            SELECT period, provider_code, treatment_function_code FROM new_periods
            UNION
            SELECT period, provider_code, treatment_function_code FROM nonadmitted
        )
        ORDER BY period, provider_code, treatment_function_code
    """)
    
    all_combinations = source_cursor.fetchall()
    print(f"Found {len(all_combinations):,} unique period/provider/treatment combinations")
    
    # Process in batches to avoid memory issues
    batch_size = 1000
    target_cursor = conn.cursor()
    
    for i in range(0, len(all_combinations), batch_size):
        batch = all_combinations[i:i + batch_size]
        
        # For each combination, get the data from all tables
        for period, provider_code, treatment_function_code in batch:
            # Get data from each table
            incomplete_data = get_incomplete_data(source_cursor, period, provider_code, treatment_function_code)
            admitted_data = get_admitted_data(source_cursor, period, provider_code, treatment_function_code)
            new_periods_data = get_new_periods_data(source_cursor, period, provider_code, treatment_function_code)
            nonadmitted_data = get_nonadmitted_data(source_cursor, period, provider_code, treatment_function_code)
            
            # Insert the consolidated record
            target_cursor.execute("""
                INSERT INTO metrics (
                    period, provider_code, treatment_function_code,
                    incomplete, admitted, new_periods, nonadmitted
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                period, provider_code, treatment_function_code,
                incomplete_data.get('incomplete'),
                admitted_data.get('admitted'),
                new_periods_data.get('new_periods'),
                nonadmitted_data.get('nonadmitted')
            ))
        
        if (i + batch_size) % 10000 == 0:
            print(f"Processed {i + batch_size:,} records...")
    
    # Now add the synthetic previous period columns
    print("Adding synthetic previous period columns...")
    add_synthetic_columns(conn)
    
    print("Populated metrics table with synthetic columns")


def get_incomplete_data(cursor, period, provider_code, treatment_function_code):
    """Get incomplete data for a specific combination."""
    cursor.execute("""
        SELECT Total_number_of_incomplete_pathways
        FROM incomplete
        WHERE period = ? AND provider_code = ? AND treatment_function_code = ?
    """, (period, provider_code, treatment_function_code))
    
    row = cursor.fetchone()
    if row:
        return {'incomplete': row[0]}
    return {}


def get_admitted_data(cursor, period, provider_code, treatment_function_code):
    """Get admitted data for a specific combination."""
    cursor.execute("""
        SELECT Total_number_of_completed_pathways_with_a_known_clock_start
        FROM admitted
        WHERE period = ? AND provider_code = ? AND treatment_function_code = ?
    """, (period, provider_code, treatment_function_code))
    
    row = cursor.fetchone()
    if row:
        return {'admitted': row[0]}
    return {}


def get_new_periods_data(cursor, period, provider_code, treatment_function_code):
    """Get new periods data for a specific combination."""
    cursor.execute("""
        SELECT Number_of_new_RTT_clock_starts_during_the_month
        FROM new_periods
        WHERE period = ? AND provider_code = ? AND treatment_function_code = ?
    """, (period, provider_code, treatment_function_code))
    
    row = cursor.fetchone()
    if row:
        return {'new_periods': row[0]}
    return {}


def get_nonadmitted_data(cursor, period, provider_code, treatment_function_code):
    """Get nonadmitted data for a specific combination."""
    cursor.execute("""
        SELECT Total_number_of_completed_pathways_all
        FROM nonadmitted
        WHERE period = ? AND provider_code = ? AND treatment_function_code = ?
    """, (period, provider_code, treatment_function_code))
    
    row = cursor.fetchone()
    if row:
        return {'nonadmitted': row[0]}
    return {}


def add_synthetic_columns(conn: sqlite3.Connection) -> None:
    """Add synthetic previous period columns using window functions."""
    cursor = conn.cursor()
    
    # Create a temporary table with the synthetic columns
    cursor.execute("""
        CREATE TEMPORARY TABLE metrics_with_prev AS
        SELECT 
            period, provider_code, treatment_function_code,
            incomplete, admitted, new_periods, nonadmitted,
            LAG(incomplete) OVER (
                PARTITION BY provider_code, treatment_function_code 
                ORDER BY period
            ) as incomplete_prev,
            LAG(admitted) OVER (
                PARTITION BY provider_code, treatment_function_code 
                ORDER BY period
            ) as admitted_prev,
            LAG(new_periods) OVER (
                PARTITION BY provider_code, treatment_function_code 
                ORDER BY period
            ) as new_periods_prev,
            LAG(nonadmitted) OVER (
                PARTITION BY provider_code, treatment_function_code 
                ORDER BY period
            ) as nonadmitted_prev
        FROM metrics
        ORDER BY period, provider_code, treatment_function_code
    """)
    
    # Clear the original table and insert the data with synthetic columns
    cursor.execute("DELETE FROM metrics")
    
    cursor.execute("""
        INSERT INTO metrics (
            period, provider_code, treatment_function_code,
            incomplete, admitted, new_periods, nonadmitted,
            incomplete_prev, admitted_prev, new_periods_prev, nonadmitted_prev
        )
        SELECT 
            period, provider_code, treatment_function_code,
            incomplete, admitted, new_periods, nonadmitted,
            incomplete_prev, admitted_prev, new_periods_prev, nonadmitted_prev
        FROM metrics_with_prev
    """)
    
    cursor.execute("DROP TABLE metrics_with_prev")


def create_indexes(conn: sqlite3.Connection) -> None:
    """Create indexes for better query performance."""
    indexes = [
        "CREATE INDEX idx_metrics_period ON metrics(period)",
        "CREATE INDEX idx_metrics_provider ON metrics(provider_code)",
        "CREATE INDEX idx_metrics_treatment ON metrics(treatment_function_code)",
        "CREATE INDEX idx_metrics_provider_treatment ON metrics(provider_code, treatment_function_code)",
        "CREATE INDEX idx_metrics_period_provider_treatment ON metrics(period, provider_code, treatment_function_code)",
    ]
    
    for index_sql in indexes:
        conn.execute(index_sql)
    
    print("Created performance indexes")


def main():
    """Main function to create the consolidated database."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    source_db_path = project_root / "data" / "nhs_provider_data.db"
    target_db_path = project_root / "data" / "nhs_consolidated.db"
    
    if not source_db_path.exists():
        print(f"Error: Source database not found at {source_db_path}")
        return
    
    print(f"Creating consolidated database from {source_db_path}")
    print(f"Target database: {target_db_path}")
    
    create_consolidated_database(str(source_db_path), str(target_db_path))
    
    # Verify the results
    conn = sqlite3.connect(str(target_db_path))
    try:
        cursor = conn.cursor()
        
        # Check table counts
        cursor.execute("SELECT COUNT(*) FROM providers")
        provider_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM treatments")
        treatment_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM metrics")
        metrics_count = cursor.fetchone()[0]
        
        print(f"\nDatabase created successfully!")
        print(f"Providers: {provider_count:,}")
        print(f"Treatments: {treatment_count:,}")
        print(f"Metrics records: {metrics_count:,}")
        
        # Show sample data
        print(f"\nSample metrics data:")
        cursor.execute("""
            SELECT m.period, p.provider_name, t.treatment_function_name,
                   m.incomplete, m.admitted, m.new_periods, m.nonadmitted,
                   m.incomplete_prev, m.admitted_prev
            FROM metrics m
            JOIN providers p ON m.provider_code = p.provider_code
            JOIN treatments t ON m.treatment_function_code = t.treatment_function_code
            WHERE m.incomplete IS NOT NULL
            ORDER BY m.period DESC, p.provider_name
            LIMIT 5
        """)
        
        for row in cursor.fetchall():
            print(f"  {row[0]} | {row[1][:30]:<30} | {row[2][:20]:<20} | "
                  f"inc:{row[3]:>8.0f} adm:{row[4]:>8.0f} new:{row[5]:>8.0f} non:{row[6]:>8.0f} | "
                  f"prev_inc:{row[7]:>8.0f} prev_adm:{row[8]:>8.0f}")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()

