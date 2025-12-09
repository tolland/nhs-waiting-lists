# Web scraper for NHS rtt waiting time dataset

> Note: ⚠️ Unofficial. This package provides programmatic access to publicly
> available NHS England Referral to Treatment (RTT) data. It is not affiliated
> with or endorsed by NHS England.

## Database tables

### Referral to Treatment (RTT) tables

#### all_rtt_raw

The raw data is initially imported into the all_rtt_raw table. We fix some
column names that differ between releases of the data, and downcase and remove
spaces from column names, and drop descriptive columns in favour of normalizing
the codes to auxiliary tables later. This table has duplicate provider
per-specialty, per-period as a provider can be commissioned by multiple
commissioning organisations.

* Fix variations in column names
* Downcase column names
* Drop descriptive columns
* Normalize variations in period column names

The data has a per provider, per-period, per-specialty view, with duplicates
for each of potentially multiple commissioning organisations, and then many
columns containing metrics for waiting times in buckets. The number of buckets
was previously up until 52 weeks and has more recently been increased to 104
weeks.

#### consolidated

This table consolidates the per-commissioning organisation into a single row per 
provider per period per specialty. The buckets are aggregated into totals for
each pathway type. A lag window is used to calculate the operning and closing
metrics for various pathway totals, and diffs between start and end of period.

#### pathways (admitted, incomplete, incomplete_with_dta, new_periods, nonadmitted)

These tables are the aggregated bucketed quantities for each pathway type, 
aggregated by commissioning organisation.

new_periods doesn't have buckets as its just an amount of new periods during 
that period.




## known_issues:

```
  - description: Excel auto-format converts "10-19" to "Oct-19"
    affected_files: ["Outpatients 22-23", "Outpatients 23-24"]
    fixed_in: "24-25"
    remediation: map 'Oct-19' → '10-19'
```