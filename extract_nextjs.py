#!/usr/bin/env python3
"""Extract and pretty-print embedded Next.js data from HTML files."""

import json
import re
import sys

from lxml import html

from src.spiders.feed import iter_flight_record_values


def extract_nextjs_records(html_file):
    """Return all parsed JSON record values from Next.js Flight data as a list."""
    with open(html_file, "r", encoding="utf-8") as file_handle:
        html_content = file_handle.read()

    document = html.fromstring(html_content)
    records = []

    for script_element in document.xpath("//script"):
        script_text = (script_element.text or "").strip()
        script_id = script_element.get("id")
        script_type = (script_element.get("type") or "").lower()

        if script_id == "__NEXT_DATA__":
            try:
                records.append(json.loads(script_text))
            except json.JSONDecodeError:
                pass
            continue

        if script_type.startswith("application/json"):
            try:
                records.append(json.loads(script_text))
            except json.JSONDecodeError:
                pass
            continue

        if "self.__next_f.push(" not in script_text:
            continue

        pattern = r"self\.__next_f\.push\(\s*(\[.*\])\s*\)"
        match = re.search(pattern, script_text, re.DOTALL)
        if not match:
            continue

        try:
            outer = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

        if not isinstance(outer, list) or len(outer) < 2:
            continue

        nextjs_string = outer[1]
        for _key, value in iter_flight_record_values(nextjs_string):
            records.append(value)

    return records


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_nextjs.py <html_file>")
        sys.exit(1)

    html_file = sys.argv[1]
    records = extract_nextjs_records(html_file)
    print(json.dumps(records, indent=2))
