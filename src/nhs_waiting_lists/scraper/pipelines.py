
from itemadapter import ItemAdapter
import os
import requests
from urllib.parse import urlparse
from scrapy.pipelines.files import FilesPipeline
from scrapy.http import Request
from typing import Any, Dict
from scrapy.pipelines.files import FilesPipeline
from scrapy.http import Request, Response
import re
from urllib.parse import urlparse
import os

class TutorialPipeline:
    def process_item(self, item, spider):
        return item



class MetadataFilesPipeline(FilesPipeline):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache metadata by URL
        self._url_metadata: Dict[str, Dict[str, Any]] = {}

    def get_media_requests(self, item: Dict[str, Any], info):
        for file_info in item.get(self.files_urls_field, []):
            if isinstance(file_info, dict):
                url = file_info['href']
                metadata = {
                    'filename': self.get_filename(url, item),
                    'dataset': file_info.get('dataset'),
                    'period': file_info.get('period'),
                    'link_text': file_info.get('link_text'),
                }
                self._url_metadata[url] = metadata
                yield Request(url, meta=metadata)
            else:
                yield Request(file_info)

    def get_filename(self, url, item):
        """Generate custom filename based on item data"""
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)

        # Add item-specific prefix
        title = item.get('title')

        if title:
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            return f"{safe_title}_{filename}"
        return filename

    def file_path(self, request, response=None, info=None, *, item=None):
        """Define the file storage path"""
        filename = request.meta.get('filename')
        dataset = request.meta.get('dataset')
        if filename and dataset:
            return os.path.join(dataset, filename)
        else:
            print(f"got here, missing {dataset=} or {filename=}")
        return super().file_path(request, response, info, item=item)
    # def file_path(self, request, response=None, info=None, *, item=None):
    #     """Define the file storage path"""
    #     filename = request.meta.get('filename')
    #     if filename:
    #         return filename
    #     return super().file_path(request, response, info, item=item)

    def item_completed(self, results, item, info):
        files = []
        for ok, file_info in results:
            if ok:
                # Enrich file_info with cached metadata
                url = file_info['url']
                if url in self._url_metadata:
                    file_info.update(self._url_metadata[url])
                    # Clean up cache
                    del self._url_metadata[url]
                files.append(file_info)

        item[self.files_result_field] = files
        return item