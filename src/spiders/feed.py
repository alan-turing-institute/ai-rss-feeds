"""Single configurable feed spider loaded from feeds.toml."""

import json
import math
import os
import pathlib
import re
import xml.etree.ElementTree as ET
from datetime import timezone
from typing import Optional
from urllib.parse import urljoin, urlparse

import dateparser
from jsonpath_ng.ext import parse as jsonpath_parse
import scrapy
from feedgen.feed import FeedGenerator

from src.feed_config import load_feed


class FeedSpider(scrapy.Spider):
    name = "feed"

    # Feed metadata
    feed_title: Optional[str] = None
    source_url: Optional[str] = None
    feed_link: Optional[str] = None
    feed_description: Optional[str] = None
    language: str = "en"

    # Format and extraction mode
    format: str = "html"  # "html" or "nextjs"

    # Item selectors (HTML mode)
    item_container_selector: Optional[str] = None
    item_title_selector: Optional[str] = None
    item_link_selector: Optional[str] = None
    item_date_selector: Optional[str] = None
    item_date_regex: Optional[str] = None
    item_description_selector: Optional[str] = None

    # Link handling
    item_guid_is_permalink: bool = True

    # Validation guardrails
    min_item_count: int = 1
    min_item_ratio_vs_previous: float = 0.6

    def __init__(self, feed_key=None, skip_unchanged=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Accept bool or the string "True"/"true"/"1" (Scrapy CLI passes strings)
        self.skip_unchanged = skip_unchanged in (True, "True", "true", "1")

        if not feed_key:
            raise RuntimeError("Missing required spider argument: feed_key")

        cfg = load_feed(feed_key)

        # Use the configured feed key as the logical spider name and output file stem.
        self.name = feed_key

        fields = [
            "feed_title",
            "source_url",
            "feed_link",
            "feed_description",
            "language",
            "format",
            "item_container_selector",
            "item_title_selector",
            "item_link_selector",
            "item_date_selector",
            "item_date_regex",
            "item_description_selector",
            "item_guid_is_permalink",
            "min_item_count",
            "min_item_ratio_vs_previous",
        ]

        for field in fields:
            if field in cfg:
                setattr(self, field, cfg[field])

    def start_requests(self):
        if not self.source_url:
            raise RuntimeError("Missing required spider configuration field: source_url")

        yield scrapy.Request(
            self.source_url,
            callback=self.parse,
            dont_filter=True,
            meta={"handle_httpstatus_all": True},
        )

    def parse(self, response):
        if response.status != 200:
            raise RuntimeError(
                f"Source URL returned HTTP {response.status}: {response.url}"
            )

        if self.format == "nextjs":
            items = self._parse_nextjs(response)
        elif self.format == "html":
            items = self._parse_html(response)
        else:
            raise RuntimeError(f"Unknown format: {self.format!r}")

        self._validate_and_generate_feed(items, response)

    def _validate_spider_config(self):
        required_fields = {
            "name": self.name,
            "feed_title": self.feed_title,
            "source_url": self.source_url,
        }

        if self.format == "html":
            required_fields.update({
                "item_container_selector": self.item_container_selector,
                "item_title_selector": self.item_title_selector,
                "item_link_selector": self.item_link_selector,
            })
        elif self.format == "nextjs":
            required_fields.update({
                "item_container_selector": self.item_container_selector,
                "item_title_selector": self.item_title_selector,
                "item_link_selector": self.item_link_selector,
            })

        missing = [field for field, value in required_fields.items() if not value]
        if missing:
            raise RuntimeError(
                f"Missing required spider configuration fields: {', '.join(missing)}"
            )

    def _read_previous_feed_item_count(self):
        feed_path = pathlib.Path("feeds") / f"{self.name}.xml"
        if not feed_path.exists():
            return None

        try:
            root = ET.parse(feed_path).getroot()
        except ET.ParseError as exc:
            raise RuntimeError(
                f"Failed to parse existing feed at {feed_path}: {exc}"
            ) from exc

        return len(root.findall("./channel/item"))

    def _extract_item(self, container, response):
        """Extract a single feed item from a scrapy Selector container."""

        # Title
        if not self.item_title_selector:
            return None
        title_parts = container.css(self.item_title_selector).getall()
        title = " ".join(t.strip() for t in title_parts if t.strip())
        if not title:
            return None

        # Link
        if not self.item_link_selector:
            return None
        link_values = container.css(self.item_link_selector).getall()
        if not link_values:
            return None
        link_val = link_values[0].strip()
        if not link_val:
            return None

        # If the selector returned an HTML node rather than an attr value,
        # pull the href out of it.
        if link_val.startswith("<"):
            href = container.css(self.item_link_selector + " ::attr(href)").get()
            link_val = href or ""
            if not link_val:
                return None

        # Resolve relative links against the page URL.
        link_val = urljoin(response.url, link_val)

        # Date
        date = None
        if self.item_date_selector:
            date_parts = container.css(self.item_date_selector).getall()
            date_str = " ".join(d.strip() for d in date_parts if d.strip())
            if date_str:
                date_text = self._extract_date_text(date_str)
                if date_text:
                    date = self._parse_date_utc(date_text)
        if date is None:
            return None

        # Description
        description = None
        if self.item_description_selector:
            desc_parts = container.css(self.item_description_selector).getall()
            description = " ".join(d.strip() for d in desc_parts if d.strip()) or None

        return {
            "title": title,
            "link": link_val,
            "date": date,
            "description": description,
        }

    def _parse_html(self, response):
        """Parse HTML format using CSS selectors."""
        self._validate_spider_config()

        containers = response.css(self.item_container_selector)
        container_count = len(containers)
        if container_count == 0:
            raise RuntimeError(
                f"No items matched item_container_selector={self.item_container_selector!r}"
            )

        items = []
        for container in containers:
            item = self._extract_item(container, response)
            if item is not None:
                items.append(item)

        skipped_count = container_count - len(items)
        if skipped_count:
            self.logger.warning(
                "Skipped %s/%s matched containers due to missing required fields",
                skipped_count,
                container_count,
            )

        return items

    def _parse_nextjs(self, response):
        """Parse Next.js Flight stream format using JSONPath selectors."""
        self._validate_spider_config()

        items_list = self._extract_nextjs_items(response)
        if not items_list:
            raise RuntimeError(
                f"No items matched nextjs item_container_selector={self.item_container_selector!r}"
            )

        items = []
        for item_data in items_list:
            item = self._extract_nextjs_item(item_data, response)
            if item is not None:
                items.append(item)

        return items

    def _jsonpath_values(self, query, obj):
        """Evaluate JSONPath query and return raw values."""
        expr = jsonpath_parse(query)
        return [match.value for match in expr.find(obj)]

    def _candidate_items_score(self, items):
        """Score candidate item lists, preferring fresher dated content."""
        latest_ts = None
        for item in items:
            if not isinstance(item, dict):
                continue
            for key in ("date", "publishedAt", "published_at"):
                raw = item.get(key)
                if not raw:
                    continue
                parsed = self._parse_date_utc(raw)
                if parsed is not None:
                    ts = parsed.timestamp()
                    if latest_ts is None or ts > latest_ts:
                        latest_ts = ts

        # Primary: recency. Secondary: list size.
        return (latest_ts if latest_ts is not None else float("-inf"), len(items))

    def _parse_date_utc(self, value):
        """Parse arbitrary date-like input and normalize it to UTC."""
        text = str(value).strip()

        parsed = dateparser.parse(
            text,
            settings={
                "RETURN_AS_TIMEZONE_AWARE": True,
                "TIMEZONE": "UTC",
                "TO_TIMEZONE": "UTC",
                "PREFER_DAY_OF_MONTH": "last",
            },
        )
        if parsed is None:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _extract_date_text(self, selected_text):
        """Return date text, optionally extracting it with item_date_regex."""
        text = str(selected_text).strip()
        if not text:
            return None

        if not self.item_date_regex:
            return text

        matches = list(re.finditer(self.item_date_regex, text))
        if len(matches) != 1:
            raise RuntimeError(
                "item_date_regex must match selected date text exactly once; "
                f"got {len(matches)} matches for text={text!r} and regex={self.item_date_regex!r}"
            )

        return matches[0].group(0)

    def _extract_nextjs_items(self, response):
        """Extract Next.js items by applying item_container_selector as JSONPath."""
        scripts = response.xpath('//script/text()').getall()
        if not scripts:
            raise RuntimeError("No script tags found in response")

        full_text = "".join(scripts)
        push_pattern = r'self\.__next_f\.push\(\s*(\[.*?\])\s*\)'
        decoder = json.JSONDecoder()
        candidates = []

        for match in re.finditer(push_pattern, full_text, re.DOTALL):
            try:
                outer = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

            if not isinstance(outer, list) or len(outer) < 2:
                continue

            payload = outer[1]
            if not isinstance(payload, str):
                continue

            # Parse Flight records at line boundaries and allow alphanumeric keys
            # like 2e/1c/a, which appear in Next.js payloads.
            key_matches = re.finditer(r'(^|\n)([0-9a-zA-Z]+):', payload)
            for key_match in key_matches:
                start_pos = key_match.end(2) + 1
                try:
                    parsed_obj, _ = decoder.raw_decode(payload, start_pos)
                except json.JSONDecodeError:
                    continue

                try:
                    matches = self._jsonpath_values(self.item_container_selector, parsed_obj)
                except Exception:
                    continue

                items = []
                for value in matches:
                    if isinstance(value, dict):
                        items.append(value)
                    elif isinstance(value, list):
                        items.extend(v for v in value if isinstance(v, dict))

                if items:
                    candidates.append(items)

        if not candidates:
            return []

        # Multiple matches can exist in Flight payloads; choose the freshest list.
        best_items = max(candidates, key=self._candidate_items_score)
        return best_items

    def _normalize_nextjs_link(self, link_val, response):
        """Normalize Next.js item links from absolute, relative, or slug values."""
        link_val = str(link_val).strip()
        if not link_val:
            return None

        if link_val.startswith(("http://", "https://")):
            return link_val

        if link_val.startswith("/"):
            return urljoin(response.url, link_val)

        # If query returns a slug, prefix it with current page path (e.g. /blog, /news).
        base_path = urlparse(response.url).path.rstrip("/")
        if base_path:
            return urljoin(response.url, f"{base_path}/{link_val}")

        return urljoin(response.url, link_val)

    def _first_text(self, values):
        """Return first non-empty scalar value from JSONPath results."""
        for value in values:
            if isinstance(value, (str, int, float, bool)):
                text = str(value).strip()
                if text:
                    return text
        return None

    def _extract_nextjs_item(self, item_data, response):
        """Extract a single item from Next.js JSON using JSONPath selectors."""
        try:
            if not isinstance(item_data, dict):
                return None

            title_values = self._jsonpath_values(self.item_title_selector, item_data)
            title = self._first_text(title_values)
            if not title:
                return None

            link_values = self._jsonpath_values(self.item_link_selector, item_data)
            link_raw = self._first_text(link_values)
            if not link_raw:
                # Pragmatic fallback for common slug structures when JSONPath returns no match.
                slug_val = item_data.get("slug")
                if isinstance(slug_val, dict):
                    link_raw = slug_val.get("current")
                elif isinstance(slug_val, str):
                    link_raw = slug_val

            if not link_raw:
                return None

            link = self._normalize_nextjs_link(link_raw, response)
            if not link:
                return None

            date = None
            if self.item_date_selector:
                date_values = self._jsonpath_values(self.item_date_selector, item_data)
                date_str = self._first_text(date_values)
                if not date_str:
                    for fallback_key in ("date", "publishedAt", "published_at"):
                        fallback_val = item_data.get(fallback_key)
                        if isinstance(fallback_val, (str, int, float)):
                            date_str = str(fallback_val)
                            break
                if date_str:
                    date_text = self._extract_date_text(date_str)
                    if date_text:
                        date = self._parse_date_utc(date_text)

            description = None
            if self.item_description_selector:
                desc_values = self._jsonpath_values(self.item_description_selector, item_data)
                description = self._first_text(desc_values)

            return {
                "title": title,
                "link": link,
                "date": date,
                "description": description,
            }
        except RuntimeError:
            raise
        except Exception as e:
            self.logger.warning(f"Failed to extract item from JSON: {e}")
            return None

    def _validate_and_generate_feed(self, items, response):
        """Validate extracted items and generate RSS feed."""
        item_count = len(items)
        min_count = max(1, int(self.min_item_count or 0))
        if item_count < min_count:
            raise RuntimeError(
                f"Extracted {item_count} items, below min_item_count={min_count}"
            )

        previous_count = self._read_previous_feed_item_count()
        if previous_count is not None and self.min_item_ratio_vs_previous is not None:
            ratio = float(self.min_item_ratio_vs_previous)
            if ratio > 0:
                required_from_previous = math.ceil(previous_count * ratio)
                required_count = max(min_count, required_from_previous)
                if item_count < required_count:
                    raise RuntimeError(
                        "Extracted "
                        f"{item_count} items, below required floor {required_count} "
                        f"from previous feed count {previous_count} and "
                        f"min_item_ratio_vs_previous={ratio}"
                    )

        fg = FeedGenerator()
        fg.id(self.source_url)
        fg.title(self.feed_title)
        link = self.feed_link or self.source_url
        fg.link(href=link, rel="alternate")
        fg.description(self.feed_description or self.feed_title)
        if self.language:
            fg.language(self.language)

        for item in items:
            fe = fg.add_entry()
            fe.title(item["title"])
            fe.link(href=item["link"])
            fe.guid(item["link"], permalink=bool(self.item_guid_is_permalink))

            if item.get("description"):
                fe.description(item["description"])
            if item.get("date"):
                fe.pubDate(item["date"])

        os.makedirs("feeds", exist_ok=True)
        feed_path = f"feeds/{self.name}.xml"

        if self.skip_unchanged:
            new_bytes = fg.rss_str(pretty=True)
            existing_path = pathlib.Path(feed_path)
            if existing_path.exists():
                existing_bytes = existing_path.read_bytes()
                _lastbuild_re = re.compile(rb"<lastBuildDate>[^<]*</lastBuildDate>")
                if _lastbuild_re.sub(b"", new_bytes) == _lastbuild_re.sub(b"", existing_bytes):
                    self.logger.info(
                        "Feed unchanged (ignoring lastBuildDate), skipping write: %s", feed_path
                    )
                    return
            existing_path.write_bytes(new_bytes)
        else:
            fg.rss_file(feed_path, pretty=True)
        self.logger.info("Feed written to %s", feed_path)
