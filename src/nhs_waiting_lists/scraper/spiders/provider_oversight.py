import re
from pathlib import Path
from typing import Any

import scrapy
from nhs_waiting_lists import (
    __app_name__,
)
from nhs_waiting_lists.utils.xdg import XDGBasedir
from scrapy.http import Response

files_dir = Path(XDGBasedir.get_data_dir(__app_name__)) / "files"


class ProviderOversightSpider(scrapy.Spider):
    name = "provider-oversight"

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("FILES_STORE", str(files_dir), priority="spider")

    start_urls = [
        "https://www.england.nhs.uk/long-read/nhs-oversight-framework-csv-metadata-file/",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        file_urls = []

        # Look for CSV file links on the page
        for link in response.css("a"):
            if "href" in link.attrib:
                href = link.attrib["href"]

                # Look for CSV files
                if href.endswith(".csv") or ".csv?" in href:
                    link_text = link.css("::text").get()

                    # Try to extract date/version information from the link text or URL
                    # Common patterns: YYYY-MM, YYYY/MM, or year mentions
                    period = None

                    # Try to find YYYY-MM pattern in URL or link text
                    date_match = re.search(r'(\d{4})[/-](\d{2})', href + (link_text or ""))
                    if date_match:
                        year, month = date_match.groups()
                        period = f"{year}-{month}"
                    else:
                        # Try to find just a year
                        year_match = re.search(r'(20\d{2})', href + (link_text or ""))
                        if year_match:
                            period = year_match.group(1)

                    # If no period found, use a generic identifier based on the URL
                    if not period:
                        # Extract filename from URL
                        filename = href.split('/')[-1].split('?')[0]
                        period = re.sub(r'\.csv$', '', filename)

                    print(f"Found provider oversight CSV: {link_text or href}")

                    file_urls.append({
                        "dataset": "provider-oversight",
                        "href": response.urljoin(href),  # Convert to absolute URL
                        'link_text': link_text or href,
                        'period': period,
                    })

        if file_urls:
            yield {
                'file_urls': file_urls,  # This triggers the Files Pipeline
            }
        else:
            self.logger.warning("No CSV files found on provider oversight page")
