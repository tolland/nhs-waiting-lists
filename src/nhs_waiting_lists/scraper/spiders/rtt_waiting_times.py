import re
from pathlib import Path
from typing import Any

import scrapy
from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.constants import MONTH_MAP
from nhs_waiting_lists.utils.xdg import XDGBasedir
from scrapy.http import Response

# pattern to match month and year in file name
pattern_mmmyy = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{2})'

files_dir = Path(XDGBasedir.get_data_dir(__app_name__)) / "files"

class QuotesSpider(scrapy.Spider):
    name = "rtt-waiting-times"

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("FILES_STORE", str(files_dir), priority="spider")

    start_urls = [
        "https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        file_urls = []
        for quote in response.css("a"):
            if "href" in quote.attrib:
                if "/statistical-work-areas/rtt-waiting-times/rtt-data-" in quote.attrib["href"]:
                    if re.search("rtt-data-[0-9]{4}-[0-9]{2}", quote.attrib["href"]):
                        yield response.follow(quote.attrib["href"], self.parse)
                elif "Full-CSV-data-file-" in quote.attrib["href"]:
                    match = re.search(pattern_mmmyy, quote.attrib["href"])
                    if match:
                        month_abbr, year_yy = match.groups()
                        # Convert 2-digit year to 4-digit year (assuming 20xx)
                        year_4digit = f"20{year_yy}"
                        # Convert month abbreviation to number
                        month_num = MONTH_MAP[month_abbr]
                        # Create period in YYYY-MM format
                        period = f"{year_4digit}-{month_num}"
                        
                        print(f"found zipped csv of monthly rtt WTD for period {period}")
                        file_urls.append({
                            "dataset": "rtt-waiting-times",
                            "href": quote.attrib["href"],
                            'link_text': quote.css("::text").get(),
                            'period': period,
                        })


# https://files.digital.nhs.uk/D6/4B3B73/hosp-epis-stat-admi-pla-2022-23-data.csv


        yield {
            'file_urls': file_urls,  # This triggers the Files Pipeline
        }
