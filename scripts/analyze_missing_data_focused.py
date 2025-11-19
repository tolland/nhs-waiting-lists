#!/usr/bin/env python3
"""
Focused analysis of missing data patterns in the NHS database.

This script can analyze:
1. Specific providers
2. A sample of providers
3. Providers with the most missing data
4. Overall summary statistics
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import argparse


def generate_expected_periods(start_date: str, end_date: str) -> list:
    """Generate list of expected monthly periods between start and end dates."""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    periods = []
    current = start
    while current <= end:
        periods.append(current.strftime('%Y-%m-%d'))
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    return periods


def get_overall_summary(db_path: str) -> None:
    """Get overall data summary without detailed analysis."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("NHS DATA OVERALL SUMMARY")
    print("=" * 60)
    
    # Get overall date range
    cursor.execute("""
        SELECT 
            MIN(period) as earliest_period,
            MAX(period) as latest_period,
            COUNT(DISTINCT period) as total_periods,
            COUNT(DISTINCT provider_code) as total_providers,
            COUNT(DISTINCT treatment_function_code) as total_treatments,
            COUNT(DISTINCT CONCAT(provider_code, '|', treatment_function_code)) as total_combinations
        FROM incomplete
    """)
    
    stats = cursor.fetchone()
    earliest, latest, total_periods, total_providers, total_treatments, total_combinations = stats
    
    print(f"Data range: {earliest} to {latest} ({total_periods} periods)")
    print(f"Providers: {total_providers:,}")
    print(f"Treatment functions: {total_treatments}")
    print(f"Provider/treatment combinations: {total_combinations:,}")
    
    # Expected vs actual data points
    expected_periods = generate_expected_periods(earliest, latest)
    total_expected = total_combinations * len(expected_periods)
    total_actual = sum(row[0] for row in cursor.execute("SELECT COUNT(*) FROM incomplete").fetchall())
    completeness = (total_actual / total_expected) * 100
    
    print(f"Expected data points: {total_expected:,}")
    print(f"Actual data points: {total_actual:,}")
    print(f"Overall completeness: {completeness:.1f}%")
    
    conn.close()


def analyze_provider_missing_data(db_path: str, provider_code: str) -> None:
    """Analyze missing data for a specific provider."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"=" * 60)
    print(f"MISSING DATA ANALYSIS FOR PROVIDER: {provider_code}")
    print(f"=" * 60)
    
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
        print(f"Provider {provider_code} not found!")
        return
    
    provider_name, region_code = provider_info
    print(f"Provider: {provider_name}")
    print(f"Region: {region_code}")
    
    # Get date range for this provider
    cursor.execute("""
        SELECT 
            MIN(period) as earliest_period,
            MAX(period) as latest_period,
            COUNT(DISTINCT period) as periods_with_data
        FROM incomplete
        WHERE provider_code = ?
    """, (provider_code,))
    
    date_range = cursor.fetchone()
    earliest, latest, periods_with_data = date_range
    
    print(f"Data range: {earliest} to {latest}")
    print(f"Periods with data: {periods_with_data}")
    
    # Get all treatment functions for this provider
    cursor.execute("""
        SELECT DISTINCT 
            treatment_function_code,
            COUNT(DISTINCT period) as periods_with_data
        FROM incomplete
        WHERE provider_code = ?
        GROUP BY treatment_function_code
        ORDER BY treatment_function_code
    """, (provider_code,))
    
    treatments = cursor.fetchall()
    print(f"\nTreatment functions: {len(treatments)}")
    
    # Generate expected periods
    expected_periods = generate_expected_periods(earliest, latest)
    print(f"Expected periods: {len(expected_periods)}")
    
    # Analyze missing data for each treatment
    print(f"\nTreatment Function | Periods with Data | Missing | Missing %")
    print("-" * 60)
    
    total_missing = 0
    for treatment_code, periods_with_data in treatments:
        missing_count = len(expected_periods) - periods_with_data
        missing_percent = (missing_count / len(expected_periods)) * 100
        total_missing += missing_count
        
        print(f"{treatment_code:<18} | {periods_with_data:>16} | {missing_count:>7} | {missing_percent:>8.1f}%")
    
    # Overall summary for this provider
    total_expected = len(treatments) * len(expected_periods)
    total_actual = sum(periods_with_data for _, periods_with_data in treatments)
    provider_completeness = (total_actual / total_expected) * 100
    
    print(f"\nProvider Summary:")
    print(f"  Expected data points: {total_expected}")
    print(f"  Actual data points: {total_actual}")
    print(f"  Missing data points: {total_missing}")
    print(f"  Completeness: {provider_completeness:.1f}%")
    
    conn.close()


def find_providers_with_most_missing_data(db_path: str, limit: int = 20) -> None:
    """Find providers with the most missing data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"=" * 60)
    print(f"PROVIDERS WITH MOST MISSING DATA (Top {limit})")
    print(f"=" * 60)
    
    # Get missing data summary by provider with their actual date ranges
    cursor.execute("""
        SELECT 
            provider_code,
            COUNT(DISTINCT treatment_function_code) as treatment_count,
            COUNT(DISTINCT period) as periods_with_data,
            COUNT(*) as total_records,
            MIN(period) as first_period,
            MAX(period) as last_period
        FROM incomplete
        GROUP BY provider_code
        ORDER BY provider_code
    """)
    
    provider_stats = cursor.fetchall()
    
    # Calculate missing data for each provider using their actual date range
    missing_summary = []
    for provider_code, treatment_count, periods_with_data, total_records, first_period, last_period in provider_stats:
        # Generate expected periods for this provider's date range
        expected_periods = generate_expected_periods(first_period, last_period)
        expected_data_points = treatment_count * len(expected_periods)
        missing_data_points = expected_data_points - total_records
        missing_percent = (missing_data_points / expected_data_points) * 100 if expected_data_points > 0 else 0
        
        missing_summary.append({
            'provider_code': provider_code,
            'treatment_count': treatment_count,
            'periods_with_data': periods_with_data,
            'total_records': total_records,
            'expected_data_points': expected_data_points,
            'missing_data_points': missing_data_points,
            'missing_percent': missing_percent,
            'first_period': first_period,
            'last_period': last_period
        })
    
    # Sort by missing percentage
    missing_summary.sort(key=lambda x: x['missing_percent'], reverse=True)
    
    print("Provider | Treatments | Records | Expected | Missing | Missing % | Date Range")
    print("-" * 85)
    
    for item in missing_summary[:limit]:
        date_range = f"{item['first_period']} to {item['last_period']}"
        print(f"{item['provider_code']:<8} | {item['treatment_count']:>10} | "
              f"{item['total_records']:>7} | {item['expected_data_points']:>8} | "
              f"{item['missing_data_points']:>7} | {item['missing_percent']:>8.1f}% | {date_range}")
    
    conn.close()


def analyze_sample_providers(db_path: str, sample_size: int = 10) -> None:
    """Analyze a random sample of providers."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"=" * 60)
    print(f"SAMPLE ANALYSIS ({sample_size} providers)")
    print(f"=" * 60)
    
    # Get random sample of providers
    cursor.execute("""
        SELECT DISTINCT provider_code
        FROM incomplete
        ORDER BY RANDOM()
        LIMIT ?
    """, (sample_size,))
    
    sample_providers = [row[0] for row in cursor.fetchall()]
    
    for provider_code in sample_providers:
        print(f"\n--- Provider: {provider_code} ---")
        
        # Get basic stats
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT treatment_function_code) as treatments,
                COUNT(DISTINCT period) as periods,
                MIN(period) as first_period,
                MAX(period) as last_period
            FROM incomplete
            WHERE provider_code = ?
        """, (provider_code,))
        
        stats = cursor.fetchone()
        treatments, periods, first_period, last_period = stats
        
        print(f"  Treatments: {treatments}")
        print(f"  Periods: {periods}")
        print(f"  Range: {first_period} to {last_period}")
        
        # Check for missing periods
        expected_periods = generate_expected_periods(first_period, last_period)
        missing_periods = len(expected_periods) - periods
        if missing_periods > 0:
            print(f"  Missing periods: {missing_periods}")
    
    conn.close()


def main():
    """Main function with command line arguments."""
    parser = argparse.ArgumentParser(description='Analyze missing data in NHS database')
    parser.add_argument('--provider', help='Analyze specific provider code')
    parser.add_argument('--sample', type=int, help='Analyze sample of providers')
    parser.add_argument('--worst', type=int, help='Show worst providers')
    parser.add_argument('--summary', action='store_true', help='Show overall summary only')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "data" / "nhs_provider_data.db"
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    if args.summary:
        get_overall_summary(str(db_path))
    elif args.provider:
        analyze_provider_missing_data(str(db_path), args.provider)
    elif args.worst:
        find_providers_with_most_missing_data(str(db_path), args.worst)
    elif args.sample:
        analyze_sample_providers(str(db_path), args.sample)
    else:
        # Default: show summary and sample
        get_overall_summary(str(db_path))
        print()
        analyze_sample_providers(str(db_path), 10)


if __name__ == "__main__":
    main()
