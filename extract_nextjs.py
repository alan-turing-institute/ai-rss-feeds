#!/usr/bin/env python3
"""Extract and pretty-print embedded Next.js data from HTML files."""

import sys
import json
import re
from pprint import pprint



def iter_flight_record_values(nextjs_string):
    """Yield (key, value) pairs parsed from a Next.js Flight payload string.

    Records are emitted as `<key>:<value>` and typically begin at line starts.
    This parser anchors to line boundaries to avoid false matches in URLs like
    `https://...`, and accepts alphanumeric keys (e.g. `2e`, `1c`, `a`).
    """
    decoder = json.JSONDecoder()
    pos = 0
    length = len(nextjs_string)

    while pos < length:
        # Find next record boundary: start of string or just after newline.
        if pos > 0:
            newline_pos = nextjs_string.find("\n", pos)
            if newline_pos == -1:
                break
            pos = newline_pos + 1

        key_start = pos
        while pos < length and nextjs_string[pos].isalnum():
            pos += 1

        # Expect at least one key character, then a colon.
        if pos == key_start or pos >= length or nextjs_string[pos] != ":":
            continue

        key = nextjs_string[key_start:pos]
        value_start = pos + 1

        # Flight records like I[...] / T... are references, not JSON values.
        if value_start < length and nextjs_string[value_start] in {"I", "T", "H"}:
            pos = value_start
            continue

        try:
            value, _ = decoder.raw_decode(nextjs_string, value_start)
            yield key, value
        except json.JSONDecodeError:
            # Skip malformed/non-JSON records and continue scanning.
            pass


def extract_nextjs_data(html_file):
    """Extract Next.js data from HTML file and pretty-print it."""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Find all script tags with self.__next_f.push(...)
    pattern = r'self\.__next_f\.push\(\s*(\[.*?\])\s*\)'
    matches = re.finditer(pattern, html_content, re.DOTALL)
    
    found_any = False
    
    for match in matches:
        json_str = match.group(1)
        try:
            # Parse the outer JSON array [number, string]
            outer = json.loads(json_str)
            if isinstance(outer, list) and len(outer) >= 2:
                number = outer[0]
                nextjs_string = outer[1]
                
                found_any = True
                print(f"\n{'='*60}")
                print(f"Chunk {number}")
                print(f"{'='*60}")
                
                # Parse records in the Flight payload robustly.
                parsed_count = 0
                for key, json_obj in iter_flight_record_values(nextjs_string):
                    parsed_count += 1
                    print(f"\nKey {key}:")
                    pprint(json_obj, width=100)

                if parsed_count == 0:
                    print("No decodable JSON records found in this chunk.")
        except json.JSONDecodeError as e:
            print(f"Failed to parse outer JSON array: {e}")
    
    if not found_any:
        print("No Next.js data found in HTML file.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_nextjs.py <html_file>")
        sys.exit(1)
    
    html_file = sys.argv[1]
    extract_nextjs_data(html_file)
