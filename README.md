# Web scraper for NHS rtt waiting time dataset

> Note: ⚠️ Unofficial. This package provides programmatic access to publicly 
> available NHS England Referral to Treatment (RTT) data. It is not affiliated 
> with or endorsed by NHS England.





## known_issues:
```
  - description: Excel auto-format converts "10-19" to "Oct-19"
    affected_files: ["Outpatients 22-23", "Outpatients 23-24"]
    fixed_in: "24-25"
    remediation: map 'Oct-19' → '10-19'
```