import re
from typing import Any
import sys
from pathlib import Path
from typing import Annotated, Optional
import scrapy
from nhs_waiting_lists.utils.xdg import XDGBasedir
from scrapy.http import Response
from nhs_waiting_lists import (
    __app_name__,
)

# pattern to match month and year in file name
pattern_mmmyy = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{2})'
# extract the format of the file
r_pla = r'([0-9]{4})-([0-9]{2})-(?:data|tab(?:%20v2)?)\.(?:csv|xlsx?m?)'

files_dir = Path(XDGBasedir.get_data_dir(__app_name__)) / "files"

class OutpatientActivitySpider(scrapy.Spider):
    name = "outpatient-activity"


    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("FILES_STORE", str(files_dir), priority="spider")

    start_urls = [
        "https://digital.nhs.uk/data-and-information/publications/statistical/hospital-outpatient-activity",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        file_urls = []
        for quote in response.css("a"):
            if "href" in quote.attrib:
                if "/data-and-information/publications/statistical/hospital-outpatient-activity" in \
                        quote.attrib["href"] and "title" in quote.attrib and quote.attrib["title"].startswith(
                        "Hospital Outpatient Activity"):
                    if re.search("/[0-9]{4}-[0-9]{2}", quote.attrib["href"]):
                        yield response.follow(response.urljoin(quote.attrib["href"]), self.parse)
                elif "/hosp-epis-stat-outp-pla" in quote.attrib["href"]:
                    match = re.search(r_pla, quote.attrib["href"])
                    if match:
                        year_yyyy, month_mm = match.groups()
                        period = f"{year_yyyy}-{month_mm}"
                        file_urls.append({
                            "dataset": "outpatient-activity",
                            "href": quote.attrib["href"],
                            'link_text': quote.css("::text").get(),
                            'period': period,
                        })

        # https://files.digital.nhs.uk/D6/4B3B73/hosp-epis-stat-admi-pla-2022-23-data.csv

        yield {
            'file_urls': file_urls,  # This triggers the Files Pipeline
        }
