#!/usr/bin/env python3
"""
Analyze provider code issues in the NHS database.

This script generates a comprehensive report of provider codes that have:
- Multiple provider names
- Multiple region codes
- Temporal changes that need manual review
"""

import sqlite3
import pandas as pd
from pathlib import Path


def analyze_provider_issues(db_path: str) -> None:
    """Generate a comprehensive report of provider issues."""
    
    conn = sqlite3.connect(db_path)
    
    print("=" * 80)
    print("NHS PROVIDER DATA QUALITY ANALYSIS")
    print("=" * 80)
    
    # Overall statistics
    print("\n1. OVERALL STATISTICS")
    print("-" * 40)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT provider_code) as unique_codes,
            COUNT(DISTINCT provider_name) as unique_names,
            COUNT(DISTINCT region_code) as unique_regions,
            COUNT(DISTINCT CONCAT(provider_code, '|', provider_name)) as unique_code_name_combos,
            COUNT(DISTINCT CONCAT(provider_code, '|', region_code, '|', provider_name)) as unique_full_combos
        FROM incomplete
    """)
    
    stats = cursor.fetchone()
    print(f"Unique provider codes: {stats[0]:,}")
    print(f"Unique provider names: {stats[1]:,}")
    print(f"Unique regions: {stats[2]:,}")
    print(f"Unique code+name combinations: {stats[3]:,}")
    print(f"Unique code+region+name combinations: {stats[4]:,}")
    
    # Provider codes with multiple names
    print("\n2. PROVIDER CODES WITH MULTIPLE NAMES")
    print("-" * 50)
    
    cursor.execute("""
        SELECT 
            provider_code,
            COUNT(DISTINCT provider_name) as name_count,
            COUNT(DISTINCT region_code) as region_count,
            GROUP_CONCAT(DISTINCT provider_name) as names,
            GROUP_CONCAT(DISTINCT region_code) as regions
        FROM incomplete
        GROUP BY provider_code
        HAVING name_count > 1
        ORDER BY name_count DESC, region_count DESC
    """)
    
    multi_name_providers = cursor.fetchall()
    print(f"Found {len(multi_name_providers)} provider codes with multiple names")
    
    for row in multi_name_providers:
        print(f"\nProvider Code: {row[0]}")
        print(f"  Names ({row[1]}): {row[3]}")
        print(f"  Regions ({row[2]}): {row[4]}")
    
    # Provider codes with multiple regions
    print("\n3. PROVIDER CODES WITH MULTIPLE REGIONS")
    print("-" * 50)
    
    cursor.execute("""
        SELECT 
            provider_code,
            COUNT(DISTINCT region_code) as region_count,
            COUNT(DISTINCT provider_name) as name_count,
            GROUP_CONCAT(DISTINCT region_code) as regions,
            GROUP_CONCAT(DISTINCT provider_name) as names
        FROM incomplete
        GROUP BY provider_code
        HAVING region_count > 1
        ORDER BY region_count DESC, name_count DESC
    """)
    
    multi_region_providers = cursor.fetchall()
    print(f"Found {len(multi_region_providers)} provider codes with multiple regions")
    
    for row in multi_region_providers:
        print(f"\nProvider Code: {row[0]}")
        print(f"  Regions ({row[1]}): {row[3]}")
        print(f"  Names ({row[2]}): {row[4]}")
    
    # Detailed temporal analysis for problematic cases
    print("\n4. DETAILED TEMPORAL ANALYSIS")
    print("-" * 50)
    print("Analyzing the most complex cases...")
    
    # Get the most complex cases (highest combination count)
    cursor.execute("""
        SELECT 
            provider_code,
            COUNT(DISTINCT CONCAT(provider_name, '|', region_code)) as combo_count
        FROM incomplete
        GROUP BY provider_code
        HAVING combo_count > 2
        ORDER BY combo_count DESC
        LIMIT 10
    """)
    
    complex_cases = cursor.fetchall()
    
    for provider_code, combo_count in complex_cases:
        print(f"\n--- Provider Code: {provider_code} ({combo_count} combinations) ---")
        
        cursor.execute("""
            SELECT 
                region_code,
                provider_name,
                COUNT(*) as records,
                MIN(period) as first_period,
                MAX(period) as last_period
            FROM incomplete
            WHERE provider_code = ?
            GROUP BY region_code, provider_name
            ORDER BY first_period, region_code, provider_name
        """, (provider_code,))
        
        details = cursor.fetchall()
        
        for detail in details:
            region, name, records, first, last = detail
            print(f"  {region} | {name[:50]:<50} | {records:>4} records | {first} to {last}")
    
    # Potential data quality issues (same code, different names, overlapping periods)
    print("\n5. POTENTIAL DATA QUALITY ISSUES")
    print("-" * 50)
    print("Cases where same provider code has different names in overlapping periods...")
    
    cursor.execute("""
        WITH provider_periods AS (
            SELECT 
                provider_code,
                provider_name,
                region_code,
                MIN(period) as first_period,
                MAX(period) as last_period
            FROM incomplete
            GROUP BY provider_code, provider_name, region_code
        ),
        overlapping AS (
            SELECT 
                p1.provider_code,
                p1.provider_name as name1,
                p1.region_code as region1,
                p1.first_period as start1,
                p1.last_period as end1,
                p2.provider_name as name2,
                p2.region_code as region2,
                p2.first_period as start2,
                p2.last_period as end2
            FROM provider_periods p1
            JOIN provider_periods p2 ON p1.provider_code = p2.provider_code
            WHERE p1.provider_name != p2.provider_name
            AND (
                (p1.first_period <= p2.last_period AND p1.last_period >= p2.first_period)
                OR (p2.first_period <= p1.last_period AND p2.last_period >= p1.first_period)
            )
        )
        SELECT DISTINCT
            provider_code,
            name1,
            region1,
            start1,
            end1,
            name2,
            region2,
            start2,
            end2
        FROM overlapping
        ORDER BY provider_code, start1
    """)
    
    overlapping_cases = cursor.fetchall()
    
    if overlapping_cases:
        print(f"Found {len(overlapping_cases)} potential overlapping cases:")
        for case in overlapping_cases:
            provider_code, name1, region1, start1, end1, name2, region2, start2, end2 = case
            print(f"\n  Provider: {provider_code}")
            print(f"    {name1[:40]:<40} ({region1}) {start1} to {end1}")
            print(f"    {name2[:40]:<40} ({region2}) {start2} to {end2}")
    else:
        print("No overlapping cases found - all name changes appear to be sequential.")
    
    # Summary recommendations
    print("\n6. SUMMARY & RECOMMENDATIONS")
    print("-" * 50)
    print("Based on this analysis:")
    print(f"• {len(multi_name_providers)} provider codes have multiple names (likely legitimate renames)")
    print(f"• {len(multi_region_providers)} provider codes have multiple regions (check for boundary changes)")
    print(f"• {len(complex_cases)} provider codes have complex combinations (manual review recommended)")
    
    if overlapping_cases:
        print(f"• {len(overlapping_cases)} potential data quality issues found (overlapping periods)")
        print("  → These should be investigated as they may indicate data errors")
    else:
        print("• No overlapping periods found - all changes appear sequential")
    
    print("\nRecommendations:")
    print("1. Review the complex cases (section 4) to verify they represent legitimate changes")
    print("2. Check region changes to confirm they align with NHS boundary changes")
    print("3. For the consolidated database, consider using the most recent name/region")
    print("4. Document any data quality issues found for future reference")
    
    conn.close()


def main():
    """Main function."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "data" / "nhs_provider_data.db"
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    analyze_provider_issues(str(db_path))


if __name__ == "__main__":
    main()
