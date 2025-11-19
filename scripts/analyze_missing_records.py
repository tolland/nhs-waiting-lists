#!/usr/bin/env python3
"""
Analyze missing records at the individual data point level.

This script identifies missing records within periods for specific providers.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


def analyze_missing_records_for_provider(db_path: str, provider_code: str) -> None:
    """Analyze missing records for a specific provider."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print(f"MISSING RECORDS ANALYSIS FOR PROVIDER: {provider_code}")
    print("=" * 80)
    
    # Get provider info
    cursor.execute("""
        SELECT DISTINCT provider_name, region_code
        FROM incomplete 
        WHERE provider_code = ?
        ORDER BY period DESC
        LIMIT 1
    """, (provider_code,))
    
    provider_info = cursor.fetchone()
    if not provider_info:
        print(f"❌ Provider {provider_code} not found in data!")
        return
    
    provider_name, region_code = provider_info
    print(f"Name: {provider_name}")
    print(f"Region: {region_code}")
    
    # Get date range for this provider
    cursor.execute("""
        SELECT 
            MIN(period) as earliest_period,
            MAX(period) as latest_period,
            COUNT(DISTINCT period) as periods_with_data,
            COUNT(DISTINCT treatment_function_code) as treatment_count,
            COUNT(*) as total_records
        FROM incomplete
        WHERE provider_code = ?
    """, (provider_code,))
    
    stats = cursor.fetchone()
    earliest_prov, latest_prov, periods_with_data, treatment_count, total_records = stats
    
    print(f"Data range: {earliest_prov} to {latest_prov}")
    print(f"Periods with data: {periods_with_data}")
    print(f"Treatment functions: {treatment_count}")
    print(f"Total records: {total_records}")
    
    # Get all periods for this provider
    cursor.execute("""
        SELECT DISTINCT period 
        FROM incomplete 
        WHERE provider_code = ?
        ORDER BY period
    """, (provider_code,))
    
    actual_periods = [row[0] for row in cursor.fetchall()]
    
    # Get all treatment functions for this provider
    cursor.execute("""
        SELECT DISTINCT treatment_function_code
        FROM incomplete
        WHERE provider_code = ?
        ORDER BY treatment_function_code
    """, (provider_code,))
    
    treatment_functions = [row[0] for row in cursor.fetchall()]
    
    print(f"\nExpected combinations: {len(actual_periods)} periods × {len(treatment_functions)} treatments = {len(actual_periods) * len(treatment_functions)}")
    print(f"Actual records: {total_records}")
    print(f"Missing records: {len(actual_periods) * len(treatment_functions) - total_records}")
    
    # Find missing combinations
    print(f"\n{'='*80}")
    print("MISSING RECORD COMBINATIONS")
    print(f"{'='*80}")
    
    # Get all existing combinations
    cursor.execute("""
        SELECT period, treatment_function_code
        FROM incomplete
        WHERE provider_code = ?
        ORDER BY period, treatment_function_code
    """, (provider_code,))
    
    existing_combinations = set((row[0], row[1]) for row in cursor.fetchall())
    
    # Find missing combinations
    missing_combinations = []
    for period in actual_periods:
        for treatment in treatment_functions:
            if (period, treatment) not in existing_combinations:
                missing_combinations.append((period, treatment))
    
    if not missing_combinations:
        print("✅ No missing record combinations found!")
    else:
        print(f"Found {len(missing_combinations)} missing record combinations:")
        print()
        
        # Group by period to see patterns
        missing_by_period = {}
        for period, treatment in missing_combinations:
            if period not in missing_by_period:
                missing_by_period[period] = []
            missing_by_period[period].append(treatment)
        
        print("Missing records by period:")
        print("Period       | Missing Treatments")
        print("-" * 50)
        
        for period in sorted(missing_by_period.keys()):
            missing_treatments = missing_by_period[period]
            treatments_str = ", ".join(missing_treatments)
            print(f"{period} | {treatments_str}")
        
        # Group by treatment to see patterns
        print(f"\nMissing records by treatment function:")
        print("Treatment | Missing Periods")
        print("-" * 40)
        
        missing_by_treatment = {}
        for period, treatment in missing_combinations:
            if treatment not in missing_by_treatment:
                missing_by_treatment[treatment] = []
            missing_by_treatment[treatment].append(period)
        
        for treatment in sorted(missing_by_treatment.keys()):
            missing_periods = missing_by_treatment[treatment]
            if len(missing_periods) <= 10:
                periods_str = ", ".join(missing_periods)
            else:
                periods_str = f"{', '.join(missing_periods[:5])}, ..., {', '.join(missing_periods[-5:])}"
            print(f"{treatment:<9} | {periods_str}")
    
    # Check for patterns in the data
    print(f"\n{'='*80}")
    print("DATA PATTERN ANALYSIS")
    print(f"{'='*80}")
    
    # Check if missing data is in specific tables
    tables = ['incomplete', 'admitted', 'new_periods', 'nonadmitted']
    
    for table in tables:
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM {table}
            WHERE provider_code = ?
        """, (provider_code,))
        
        count = cursor.fetchone()[0]
        print(f"{table:<12}: {count:>6} records")
    
    # Check for NULL values in key fields
    print(f"\nNULL value analysis:")
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(Total_number_of_incomplete_pathways) as incomplete_not_null,
            COUNT(Total_number_of_completed_pathways_with_a_known_clock_start) as admitted_not_null,
            COUNT(Number_of_new_RTT_clock_starts_during_the_month) as new_periods_not_null,
            COUNT(Total_number_of_completed_pathways_all) as nonadmitted_not_null
        FROM (
            SELECT 
                i.Total_number_of_incomplete_pathways,
                a.Total_number_of_completed_pathways_with_a_known_clock_start,
                np.Number_of_new_RTT_clock_starts_during_the_month,
                na.Total_number_of_completed_pathways_all
            FROM incomplete i
            LEFT JOIN admitted a ON (
                i.period = a.period AND 
                i.provider_code = a.provider_code AND 
                i.treatment_function_code = a.treatment_function_code
            )
            LEFT JOIN new_periods np ON (
                i.period = np.period AND 
                i.provider_code = np.provider_code AND 
                i.treatment_function_code = np.treatment_function_code
            )
            LEFT JOIN nonadmitted na ON (
                i.period = na.period AND 
                i.provider_code = na.provider_code AND 
                i.treatment_function_code = na.treatment_function_code
            )
            WHERE i.provider_code = ?
        )
    """, (provider_code,))
    
    null_stats = cursor.fetchone()
    total, incomplete_not_null, admitted_not_null, new_periods_not_null, nonadmitted_not_null = null_stats
    
    print(f"Total records analyzed: {total}")
    print(f"Incomplete (not NULL): {incomplete_not_null} ({incomplete_not_null/total*100:.1f}%)")
    print(f"Admitted (not NULL): {admitted_not_null} ({admitted_not_null/total*100:.1f}%)")
    print(f"New periods (not NULL): {new_periods_not_null} ({new_periods_not_null/total*100:.1f}%)")
    print(f"Nonadmitted (not NULL): {nonadmitted_not_null} ({nonadmitted_not_null/total*100:.1f}%)")
    
    conn.close()


def main():
    """Main function."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python analyze_missing_records.py <provider_code>")
        print("Example: python analyze_missing_records.py RAJ")
        return
    
    provider_code = sys.argv[1].upper()
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "data" / "nhs_provider_data.db"
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    analyze_missing_records_for_provider(str(db_path), provider_code)


if __name__ == "__main__":
    main()
