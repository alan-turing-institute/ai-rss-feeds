#!/usr/bin/env python3
import json
import re
import sys


def walk(node, pattern, path=""):
    if isinstance(node, str):
        if pattern.search(node):
            print(path)
    elif isinstance(node, dict):
        for key, value in node.items():
            walk(value, pattern, f'{path}."{key}"')
    elif isinstance(node, list):
        for i, value in enumerate(node):
            walk(value, pattern, f"{path}.{i}")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <file.json> <regex>", file=sys.stderr)
        sys.exit(1)

    filename, regex = sys.argv[1], sys.argv[2]
    pattern = re.compile(regex)

    with open(filename) as f:
        data = json.load(f)

    walk(data, pattern)


if __name__ == "__main__":
    main()
