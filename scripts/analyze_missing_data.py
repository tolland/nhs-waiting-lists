#!/usr/bin/env python3
"""
Analyze missing data patterns in the NHS database.

This script identifies:
1. Missing periods for each provider/treatment combination
2. Providers that gained/lost treatment functions over time
3. Overall data completeness patterns
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


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


def analyze_missing_data(db_path: str) -> None:
    """Analyze missing data patterns in the NHS database."""
    
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("NHS DATA COMPLETENESS ANALYSIS")
    print("=" * 80)
    
    # Get overall date range
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            MIN(period) as earliest_period,
            MAX(period) as latest_period,
            COUNT(DISTINCT period) as total_periods
        FROM incomplete
    """)
    
    date_range = cursor.fetchone()
    earliest, latest, total_periods = date_range
    
    print(f"\n1. OVERALL DATA RANGE")
    print("-" * 40)
    print(f"Earliest period: {earliest}")
    print(f"Latest period: {latest}")
    print(f"Total periods in data: {total_periods}")
    
    # Generate expected periods
    expected_periods = generate_expected_periods(earliest, latest)
    print(f"Expected periods: {len(expected_periods)}")
    print(f"Missing periods: {len(expected_periods) - total_periods}")
    
    # Get all unique provider/treatment combinations
    cursor.execute("""
        SELECT DISTINCT 
            provider_code, 
            treatment_function_code,
            COUNT(DISTINCT period) as periods_with_data
        FROM incomplete
        GROUP BY provider_code, treatment_function_code
        ORDER BY provider_code, treatment_function_code
    """)
    
    provider_treatments = cursor.fetchall()
    print(f"\n2. PROVIDER/TREATMENT COMBINATIONS")
    print("-" * 50)
    print(f"Total unique provider/treatment combinations: {len(provider_treatments):,}")
    
    # Analyze missing data for each combination
    print(f"\n3. MISSING DATA ANALYSIS")
    print("-" * 50)
    
    missing_data_summary = []
    treatment_changes = defaultdict(list)
    
    for provider_code, treatment_code, periods_with_data in provider_treatments:
        # Get actual periods for this combination
        cursor.execute("""
            SELECT DISTINCT period 
            FROM incomplete 
            WHERE provider_code = ? AND treatment_function_code = ?
            ORDER BY period
        """, (provider_code, treatment_code))
        
        actual_periods = [row[0] for row in cursor.fetchall()]
        missing_periods = [p for p in expected_periods if p not in actual_periods]
        
        if missing_periods:
            missing_data_summary.append({
                'provider_code': provider_code,
                'treatment_code': treatment_code,
                'periods_with_data': periods_with_data,
                'missing_periods': len(missing_periods),
                'missing_percent': (len(missing_periods) / len(expected_periods)) * 100,
                'first_missing': missing_periods[0] if missing_periods else None,
                'last_missing': missing_periods[-1] if missing_periods else None
            })
    
    # Sort by missing percentage
    missing_data_summary.sort(key=lambda x: x['missing_percent'], reverse=True)
    
    print(f"Combinations with missing data: {len(missing_data_summary):,}")
    print(f"Combinations with complete data: {len(provider_treatments) - len(missing_data_summary):,}")
    
    # Show worst cases
    print(f"\nTop 20 combinations with most missing data:")
    print("Provider | Treatment | Missing % | Missing Count | First Missing | Last Missing")
    print("-" * 80)
    
    for item in missing_data_summary[:20]:
        print(f"{item['provider_code']:<8} | {item['treatment_code']:<9} | "
              f"{item['missing_percent']:>8.1f}% | {item['missing_periods']:>12} | "
              f"{item['first_missing'] or 'N/A':<12} | {item['last_missing'] or 'N/A'}")
    
    # Analyze treatment function changes over time
    print(f"\n4. TREATMENT FUNCTION CHANGES OVER TIME")
    print("-" * 50)
    
    # Get treatment function timeline for each provider
    cursor.execute("""
        SELECT 
            provider_code,
            treatment_function_code,
            MIN(period) as first_period,
            MAX(period) as last_period,
            COUNT(DISTINCT period) as periods_active
        FROM incomplete
        GROUP BY provider_code, treatment_function_code
        ORDER BY provider_code, first_period
    """)
    
    treatment_timeline = cursor.fetchall()
    
    # Group by provider to find changes
    provider_treatments = defaultdict(list)
    for row in treatment_timeline:
        provider_code, treatment_code, first_period, last_period, periods_active = row
        provider_treatments[provider_code].append({
            'treatment_code': treatment_code,
            'first_period': first_period,
            'last_period': last_period,
            'periods_active': periods_active
        })
    
    # Find providers with treatment function changes
    providers_with_changes = []
    for provider_code, treatments in provider_treatments.items():
        if len(treatments) > 1:
            # Sort by first period
            treatments.sort(key=lambda x: x['first_period'])
            
            # Check for gaps or overlaps
            changes = []
            for i in range(len(treatments) - 1):
                current = treatments[i]
                next_treatment = treatments[i + 1]
                
                # Check if there's a gap or if treatments overlap
                current_end = datetime.strptime(current['last_period'], '%Y-%m-%d')
                next_start = datetime.strptime(next_treatment['first_period'], '%Y-%m-%d')
                
                if next_start > current_end + timedelta(days=32):  # More than a month gap
                    changes.append(f"Gap between {current['treatment_code']} and {next_treatment['treatment_code']}")
                elif next_start < current_end - timedelta(days=32):  # Overlap
                    changes.append(f"Overlap between {current['treatment_code']} and {next_treatment['treatment_code']}")
            
            if changes:
                providers_with_changes.append({
                    'provider_code': provider_code,
                    'treatment_count': len(treatments),
                    'changes': changes,
                    'treatments': treatments
                })
    
    print(f"Providers with treatment function changes: {len(providers_with_changes)}")
    
    # Show examples of providers with changes
    print(f"\nExamples of providers with treatment function changes:")
    for provider in providers_with_changes[:10]:
        print(f"\nProvider: {provider['provider_code']} ({provider['treatment_count']} treatments)")
        for change in provider['changes']:
            print(f"  - {change}")
        print("  Treatment timeline:")
        for treatment in provider['treatments']:
            print(f"    {treatment['treatment_code']}: {treatment['first_period']} to {treatment['last_period']} "
                  f"({treatment['periods_active']} periods)")
    
    # Analyze data completeness by period
    print(f"\n5. DATA COMPLETENESS BY PERIOD")
    print("-" * 50)
    
    cursor.execute("""
        SELECT 
            period,
            COUNT(DISTINCT provider_code) as providers,
            COUNT(DISTINCT treatment_function_code) as treatments,
            COUNT(DISTINCT CONCAT(provider_code, '|', treatment_function_code)) as combinations
        FROM incomplete
        GROUP BY period
        ORDER BY period
    """)
    
    period_stats = cursor.fetchall()
    
    print("Period       | Providers | Treatments | Combinations")
    print("-" * 50)
    for period, providers, treatments, combinations in period_stats:
        print(f"{period} | {providers:>9} | {treatments:>10} | {combinations:>12}")
    
    # Find periods with unusually low data
    if period_stats:
        avg_combinations = sum(row[3] for row in period_stats) / len(period_stats)
        low_data_periods = [row for row in period_stats if row[3] < avg_combinations * 0.8]
        
        if low_data_periods:
            print(f"\nPeriods with unusually low data (< 80% of average):")
            for period, providers, treatments, combinations in low_data_periods:
                print(f"  {period}: {combinations} combinations (avg: {avg_combinations:.0f})")
    
    # Summary statistics
    print(f"\n6. SUMMARY STATISTICS")
    print("-" * 50)
    
    total_expected_combinations = len(provider_treatments) * len(expected_periods)
    total_actual_combinations = sum(row[2] for row in provider_treatments)
    overall_completeness = (total_actual_combinations / total_expected_combinations) * 100
    
    print(f"Total expected data points: {total_expected_combinations:,}")
    print(f"Total actual data points: {total_actual_combinations:,}")
    print(f"Overall data completeness: {overall_completeness:.1f}%")
    print(f"Missing data points: {total_expected_combinations - total_actual_combinations:,}")
    
    # Data quality recommendations
    print(f"\n7. DATA QUALITY RECOMMENDATIONS")
    print("-" * 50)
    
    if len(missing_data_summary) > 0:
        high_missing = [item for item in missing_data_summary if item['missing_percent'] > 50]
        print(f"• {len(high_missing)} combinations have >50% missing data - investigate these")
    
    if len(providers_with_changes) > 0:
        print(f"• {len(providers_with_changes)} providers have treatment function changes - verify these are legitimate")
    
    if len(low_data_periods) > 0:
        print(f"• {len(low_data_periods)} periods have unusually low data - check for data collection issues")
    
    print(f"• Consider excluding combinations with >80% missing data from analysis")
    print(f"• Document treatment function changes for business context")
    print(f"• Investigate periods with low data completeness")
    
    conn.close()


def main():
    """Main function."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "data" / "nhs_provider_data.db"
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    analyze_missing_data(str(db_path))


if __name__ == "__main__":
    main()
