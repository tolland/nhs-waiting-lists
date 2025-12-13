# Web scraper for NHS rtt waiting time dataset

> Warning: This is a work in progress.

> Note: ⚠️ Unofficial. This package provides programmatic access to publicly
> available NHS England Referral to Treatment (RTT) data. It is not affiliated
> with or endorsed by NHS England.

## Background

The NHS has published Referral to Treatment (RTT) waiting times data since 2007
in various formats.
[Since 2015-16](https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/)
financial year they have been providing this in a single csv file per reporting
period. Which makes it somewhat easier to analyse. Before that it was published
as excel spreadsheets.
The dataset is based on monthly submissions from organisations providing
consultant-led care under the Open Government Licence v3.0. Each submission
reports the number of
new RTT referrals, the number of pathways reaching a clock-stop during the month
either due to treatment or for non-clinical reasons, and the number of
incomplete pathways remaining at month-end for each NHS provider.

The aggregate of these incomplete pathways is widely reported as the NHS
“waiting list”. The purpose of this package is to allow easy access to this
data using pandas objects for charting and report building.

### Basic Usage

The package ships the core data in a sqlite database. This includes the NHS
acute trusts starting from 2023-01, per provider totals and pathway metrics 
which is used under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) referenced on the NHS RTT website.

In this case you can simply query the data from the package object:

```python
import nhs_waiting_lists as nhs

start_period = "2024-01"
end_period = "2024-12"
summary_df = nhs.get_consolidated_df(
    start_period,
    end_period,
    nhs.PROVIDER_CODES,
    nhs.TREATMENT_CODES,
).groupby(["period", "provider"]).sum()
summary_df.head()
```

will output something like:

```
      period  new_periods  completed  incomplete
0 2024-01-01        18812      15598       60893
1 2024-02-01        18924      14810       62414
2 2024-03-01        17715      14382       62324
3 2024-04-01        18755      15027       60982
4 2024-05-01        19161      15424       61709
```

### Extended Usage

The RTT dataset has data in various formats going back to 2007. This package has
been tested to work with the data going back to 2016-17. This section describes
how to use the package to scrape and import the data to include earlier periods
and to include data from other datasets for comparison by period and provider.
For example an interesting comparison is the unreported removal rate per
provider
from the rtt dataset compared to the published patient Did-not-attend (DNAs)
data
from the outpatients activity dataset.

This package provides three main functions to
make the data more accessible:

1. RTT source file scraper. This gets the latest data from the NHS website.
2. Source file importer and parser. This recognises the format of the data and
   converts it into a continuous time series of waiting times in sqlite format,
   ready for analysis.
3. The data is exposed as a package object, which can be queried using pandas
   functions.

## Understanding RTT Pathways and Patient Waits

An RTT pathway tracks an individual patient's journey from referral to
treatment. Each pathway has a "clock start" (when the referral is made) and a
"clock stop" (when treatment begins or the pathway ends for non-clinical
reasons).

The dataset reports incomplete pathways - these represent patients still
waiting for treatment. While it's common to refer to this as the number of
"patients waiting", this isn't strictly accurate. In practice, most patients
are on a single pathway, but some patients may have multiple concurrent
pathways for different conditions or treatments. Currently, there is no
reliable way to quantify what proportion of pathways correspond to unique
patients versus patients with multiple active pathways.

For practical purposes, the incomplete pathways count serves as a close
approximation of patients waiting, but this limitation should be kept in mind
when interpreting the data or making claims about patient numbers.

## Limitations

### Dataset Quality and Temporal Reliability

**The data quality varies significantly over time:**

* **2023 onwards (Recommended)**: The data is mostly reliable from the start of
  2023. This is the recommended period for analysis.

* **2022**: Missing submissions from RDU (NHS England Regional Teams) and R0A
  (provider type) organisations affect data completeness for this year. Use
  with caution.

* **Pre-2022**: Increasingly unreliable due to field mapping inconsistencies,
  trust mergers, splits, renaming, and lower quality submissions. Historical
  analysis before 2022 should account for these data quality issues.

* **Bucketing changes**: The wait time bucketing changed from >52 weeks to >104
  weeks in 2021. Querying across these buckets will require manual processing.

### Technical and Data Scope Limitations

* This package was developed and tested on Linux. It may not work on Windows
  or Mac, but probably will with minor changes.
* There are some periods where providers did not submit data. Estimates for
  those datapoints are provided by the NHS; however, this package does not
  include them, so some years will underestimate the number of incomplete
  pathways.
* This package is mainly focused on the acute trust providers due to the
  availability of the types and subtypes of these providers via the NHS
  oversight
  framework publications. Therefore, you can do something like:
  `nhs.get_df(start_period="2024-01").query("provider.type == 'Acute Trust'")`
  but you can't do that for say independent
  specialists, because the NHS doesn't publish that data in an easy-to-use
  format.
* The data becomes increasingly more unreliable as you go back further in time.
  Due to trust mergers, splits, renaming and low quality submissions.
* Bucketing of the data changed from greater than 52 weeks to greater than
  104 weeks in 2021. Querying across these buckets will require some manual
  processing.

## Getting started

### Installation

Install the package using pip or uv in the regular way.

### Scraping the source files

```bash

# in general you want to pick a recent start period, and progressively backfill.
# scrapy won't re-download files that haven't changed.

# Run the scraper for the RTT data (uf you are interested in 2023-01, use 2022-12)
nhsctl scraper rtt --start_period 2022-12

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