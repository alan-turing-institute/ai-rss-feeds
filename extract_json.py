#!/usr/bin/env python3
"""Extract and pretty-print embedded JSON data from HTML files."""

import json
import sys

from scrapy.selector import Selector

from src.spiders.feed import iter_json_blobs


def extract_json_blobs(html_file):
    """Return every embedded JSON blob found in an HTML file, as a list."""
    with open(html_file, "r", encoding="utf-8") as file_handle:
        html_content = file_handle.read()

    selector = Selector(text=html_content)
    return list(iter_json_blobs(selector))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_json.py <html_file>")
        sys.exit(1)

    html_file = sys.argv[1]
    blobs = extract_json_blobs(html_file)
    print(json.dumps(blobs, indent=2))
