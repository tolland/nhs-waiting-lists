# Web scraper for NHS rtt waiting time dataset

> Warning: This is a work in progress.

> Note: ⚠️ Unofficial. This package provides programmatic access to publicly
> available NHS England Referral to Treatment (RTT) data. It is not affiliated
> with or endorsed by NHS England.

## Background

The NHS has published Referral to Treatment (RTT) waiting times data since 2007,
and is available in a readily parsable
format [since 2011](https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/)
The dataset is based on monthly submissions from organisations providing
consultant-led care under the Open Government Licence v3.0. Each submission
reports the number of
new RTT referrals, the number of pathways reaching a clock-stop during the month
either due to treatment or for non-clinical reasons, and the number of
incomplete pathways remaining at month-end for each NHS provider.

The aggregate of these incomplete pathways is widely reported as the NHS
“waiting list”. The purpose of this package is to allow easy access to this
data using pandas objects for charting and report building.

The data format and field names have slightly changed over time, making using
the data as published difficult. This package provides three main functions to
make the data more accessible:

1. RTT source file scraper. This gets the latest data from the NHS website.
2. Source file importer and parser. This recognises the format of the data and
   converts it into a continuous time series of waiting times in sqlite format,
   ready for analysis.
3. The data is exposed as a package object, which can be queried using pandas
   functions.

## Limitations

* This package was developed and tested on Linux. It may not work on Windows
  or Mac, but probably will with minor changes.
* There are some periods where providers did not submit data. Estimates for
  those
  datapoints are provided by the NHS; however, this package does not include
  them.
* This package is mainly focused on the acute trust providers due to the
  availability of the types and subtypes of these providers via the NHS
  oversight
  framework publications. Therefore you can do something like:
  `nhs.get_df(start_period="2024-01").query("provider.type == 'Acute Trust'")`
  but you can't do that for say independent
  specialists, because the NHS doesn't publish that data in an easy to use
  format.
* The data becomes increasingly more unreliable as you go back further in time.
  Due to trust mergers, splits, renaming and low quality submissions.

## Getting started

### Installation

Install the package using pip or uv in the regular way.

### Scraping the source files

```bash

# Run the scraper for the RTT data
# in general you want to pick a recent start period, as the full dataset is many GBs
nhsctl scraper rtt --start_period 2023-01

# Run the scraper for the provider codes to types mappings
nhsctl scraper providers

# Optionally, if you want to compare RTT data with outpatients activity, such as DNAs
nhsctl scraper outpatients-activity
```

This will download the latest source files and store them in the `data` folder.

### Importing the data into sqlite

The importer will read the source files and convert them into a sqlite database.

```bash
# import the raw RTT data. This is the part that fixes the formatting and column names
# It produces a table all_rtt_raw as an intermediate step, which is useful for 
# debugging missing values
# in general you want to pick a recent start period, as the full dataset is 
nhsctl import rtt-raw --start_period 2023-01



# build the summary tables. This converts the long format of a row per pathway type
# into a table with one row per period, with totals
nhsctl import rtt-metrics

# build the pathway bucket tables. This converts the many rows of different metrics
# types into a table for each metric type.
nhsctl import rtt-pathways

# Import the providers
nhsctl import providers