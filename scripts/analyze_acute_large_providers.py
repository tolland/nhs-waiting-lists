#!/usr/bin/env python3
"""
Analyze data completeness for specific Acute - Large providers.

This script focuses on the list of Acute - Large providers to check:
1. Data completeness for each provider
2. Missing periods and treatment functions
3. Patterns in missing data
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


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


def analyze_acute_large_providers(db_path: str) -> None:
    """Analyze the specific Acute - Large providers focusing on missing periods."""
    
    # List of Acute - Large providers to analyze
    acute_large_providers = [
        'RTF', 'RWF', 'RTE', 'REF', 'RWH', 'R0B', 'RVJ', 'RHW', 'RDU', 'RH8',
        'RWY', 'RXC', 'RL4', 'RDE', 'RXK', 'RXR', 'RJ2', 'RN5', 'RHU', 'RGN',
        'RWP', 'RWD', 'RAJ'
    ]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("ACUTE - LARGE PROVIDERS: MISSING PERIODS ANALYSIS")
    print("=" * 80)
    print("Focus: Identifying missing months that suggest missing source spreadsheets")
    print()
    
    # Get overall date range
    cursor.execute("SELECT MIN(period), MAX(period) FROM incomplete")
    earliest, latest = cursor.fetchone()
    expected_periods = generate_expected_periods(earliest, latest)
    
    print(f"Overall data range: {earliest} to {latest} ({len(expected_periods)} periods)")
    print(f"Analyzing {len(acute_large_providers)} Acute - Large providers")
    
    # Collect all missing periods across providers
    all_missing_periods = {}
    provider_summaries = []
    
    for provider_code in acute_large_providers:
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
            continue
        
        provider_name, region_code = provider_info
        
        # Get date range for this provider
        cursor.execute("""
            SELECT 
                MIN(period) as earliest_period,
                MAX(period) as latest_period,
                COUNT(DISTINCT period) as periods_with_data,
                COUNT(DISTINCT treatment_function_code) as treatment_count
            FROM incomplete
            WHERE provider_code = ?
        """, (provider_code,))
        
        stats = cursor.fetchone()
        earliest_prov, latest_prov, periods_with_data, treatment_count = stats
        
        # Generate expected periods for this provider's range
        expected_periods_prov = generate_expected_periods(earliest_prov, latest_prov)
        
        # Get actual periods for this provider
        cursor.execute("""
            SELECT DISTINCT period 
            FROM incomplete 
            WHERE provider_code = ?
            ORDER BY period
        """, (provider_code,))
        
        actual_periods = [row[0] for row in cursor.fetchall()]
        missing_periods = [p for p in expected_periods_prov if p not in actual_periods]
        
        # Store missing periods for cross-provider analysis
        for period in missing_periods:
            if period not in all_missing_periods:
                all_missing_periods[period] = []
            all_missing_periods[period].append(provider_code)
        
        # Store summary
        provider_summaries.append({
            'provider_code': provider_code,
            'provider_name': provider_name,
            'region_code': region_code,
            'earliest_period': earliest_prov,
            'latest_period': latest_prov,
            'periods_with_data': periods_with_data,
            'treatment_count': treatment_count,
            'missing_periods': missing_periods,
            'missing_count': len(missing_periods)
        })
    
    # Show providers with missing periods
    print(f"\n{'='*80}")
    print("PROVIDERS WITH MISSING PERIODS")
    print(f"{'='*80}")
    
    providers_with_missing = [p for p in provider_summaries if p['missing_count'] > 0]
    
    if not providers_with_missing:
        print("✅ All Acute - Large providers have complete data!")
    else:
        print(f"Found {len(providers_with_missing)} providers with missing periods:")
        print()
        
        for provider in providers_with_missing:
            print(f"🔍 {provider['provider_code']} - {provider['provider_name']}")
            print(f"   Region: {provider['region_code']}")
            print(f"   Data range: {provider['earliest_period']} to {provider['latest_period']}")
            print(f"   Missing {provider['missing_count']} periods:")
            
            # Show missing periods in a compact format
            missing_periods = provider['missing_periods']
            if len(missing_periods) <= 10:
                for period in missing_periods:
                    print(f"     {period}")
            else:
                # Show first 5 and last 5
                for period in missing_periods[:5]:
                    print(f"     {period}")
                print(f"     ... ({len(missing_periods) - 10} more) ...")
                for period in missing_periods[-5:]:
                    print(f"     {period}")
            print()
    
    # Cross-provider analysis: periods missing across multiple providers
    print(f"{'='*80}")
    print("CROSS-PROVIDER MISSING PERIODS ANALYSIS")
    print(f"{'='*80}")
    print("Periods missing across multiple providers (likely missing source spreadsheets):")
    print()
    
    # Sort by number of providers missing each period
    periods_by_missing_count = sorted(all_missing_periods.items(), key=lambda x: len(x[1]), reverse=True)
    
    if not periods_by_missing_count:
        print("✅ No missing periods found across providers!")
    else:
        print("Period       | Missing Providers | Provider Codes")
        print("-" * 70)
        
        for period, missing_providers in periods_by_missing_count:
            if len(missing_providers) > 1:  # Only show periods missing from multiple providers
                provider_codes = ", ".join(missing_providers)
                print(f"{period} | {len(missing_providers):>16} | {provider_codes}")
        
        # Summary statistics
        periods_missing_multiple = [p for p, providers in periods_by_missing_count if len(providers) > 1]
        periods_missing_single = [p for p, providers in periods_by_missing_count if len(providers) == 1]
        
        print(f"\nSummary:")
        print(f"  Periods missing from multiple providers: {len(periods_missing_multiple)}")
        print(f"  Periods missing from single providers: {len(periods_missing_single)}")
        
        if periods_missing_multiple:
            print(f"\n⚠️  These {len(periods_missing_multiple)} periods are likely due to missing source spreadsheets:")
            for period, providers in periods_missing_multiple:
                print(f"    {period}: missing from {len(providers)} providers")
    
    # Overall completeness summary
    print(f"\n{'='*80}")
    print("OVERALL COMPLETENESS SUMMARY")
    print(f"{'='*80}")
    
    if provider_summaries:
        total_expected_periods = sum(len(generate_expected_periods(p['earliest_period'], p['latest_period'])) for p in provider_summaries)
        total_actual_periods = sum(p['periods_with_data'] for p in provider_summaries)
        total_missing_periods = sum(p['missing_count'] for p in provider_summaries)
        overall_completeness = (total_actual_periods / total_expected_periods) * 100 if total_expected_periods > 0 else 0
        
        print(f"Total expected periods across all providers: {total_expected_periods:,}")
        print(f"Total actual periods: {total_actual_periods:,}")
        print(f"Total missing periods: {total_missing_periods:,}")
        print(f"Overall completeness: {overall_completeness:.1f}%")
        
        # Provider-by-provider completeness
        print(f"\nProvider Completeness:")
        for provider in sorted(provider_summaries, key=lambda x: x['missing_count'], reverse=True):
            expected = len(generate_expected_periods(provider['earliest_period'], provider['latest_period']))
            completeness = (provider['periods_with_data'] / expected) * 100 if expected > 0 else 0
            status = "✅" if provider['missing_count'] == 0 else f"⚠️ ({provider['missing_count']} missing)"
            print(f"  {provider['provider_code']}: {completeness:>5.1f}% {status}")
    
    conn.close()


def main():
    """Main function."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "data" / "nhs_provider_data.db"
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    analyze_acute_large_providers(str(db_path))


if __name__ == "__main__":
    main()
