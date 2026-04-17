#!/usr/bin/env python3
"""Extract and pretty-print embedded Next.js data from HTML files."""

import json
import re
import sys
from pprint import pprint

from lxml import html



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
        line_end = nextjs_string.find("\n", pos)
        if line_end == -1:
            line_end = length

        line = nextjs_string[pos:line_end]
        separator_idx = line.find(":")

        # Move to the next line by default to guarantee forward progress.
        next_pos = line_end + 1

        # Expect records formatted as <alnum_key>:<json_value>.
        if separator_idx <= 0:
            pos = next_pos
            continue

        key = line[:separator_idx]
        if not key.isalnum():
            pos = next_pos
            continue

        value_start = pos + separator_idx + 1

        # Flight records like I[...] / T... are references, not JSON values.
        if value_start < length and nextjs_string[value_start] in {"I", "T", "H"}:
            pos = next_pos
            continue

        try:
            value, _ = decoder.raw_decode(nextjs_string, value_start)
            yield key, value
        except json.JSONDecodeError:
            # Skip malformed/non-JSON records and continue scanning.
            pass

        pos = next_pos


def _print_json_block(title, raw_json):
    print(f"\n{'=' * 60}")
    print(title)
    print(f"{'=' * 60}")

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as error:
        print(f"Failed to parse JSON: {error}")
        print(raw_json)
        return

    pprint(parsed, width=100)


def extract_nextjs_data(html_file):
    """Extract Next.js data from HTML file and pretty-print it."""
    with open(html_file, "r", encoding="utf-8") as file_handle:
        html_content = file_handle.read()

    document = html.fromstring(html_content)

    found_any = False

    for script_element in document.xpath("//script"):
        script_text = (script_element.text or "").strip()
        script_id = script_element.get("id")
        script_type = (script_element.get("type") or "").lower()

        if script_id == "__NEXT_DATA__":
            found_any = True
            _print_json_block("__NEXT_DATA__", script_text)
            continue

        if script_type.startswith("application/json"):
            found_any = True
            _print_json_block("application/json script", script_text)
            continue

        if "self.__next_f.push(" not in script_text:
            continue

        found_any = True
        pattern = r"self\.__next_f\.push\(\s*(\[.*\])\s*\)"
        match = re.search(pattern, script_text, re.DOTALL)
        if not match:
            print("\n" + "=" * 60)
            print("Next.js Flight chunk")
            print("=" * 60)
            print("Could not parse Flight chunk payload.")
            print(script_text)
            continue

        json_str = match.group(1)
        try:
            # Parse the outer JSON array [number, string]
            outer = json.loads(json_str)
            if isinstance(outer, list) and len(outer) >= 2:
                number = outer[0]
                nextjs_string = outer[1]

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
        except json.JSONDecodeError as error:
            print(f"Failed to parse outer JSON array: {error}")

    if not found_any:
        print("No Next.js data found in HTML file.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_nextjs.py <html_file>")
        sys.exit(1)
    
    html_file = sys.argv[1]
    extract_nextjs_data(html_file)
