"""Base spider class - subclasses define selectors and feed metadata."""

import math
import os
import pathlib
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import urljoin

import dateparser
import scrapy
from feedgen.feed import FeedGenerator


class BaseFeedSpider(scrapy.Spider):
    """
    Scrapes a single page and writes an RSS 2.0 feed to feeds/<name>.xml.

    Subclasses must define:
        name              – scrapy spider name (used as the output filename)
        feed_title        – human-readable feed title
        source_url        – URL to scrape

    Subclasses should define selectors:
        item_container_selector   – CSS selector for each item's container element
        item_title_selector       – CSS selector (within container) for the title text
        item_link_selector        – CSS selector (within container) for the link;
                                    may return an href attribute value or an <a> node
        item_date_selector        – CSS selector (within container) for the date text
        item_description_selector – CSS selector (within container) for description text

    Optional overrides:
        feed_link         – canonical feed URL (defaults to source_url)
        feed_description  – feed description (defaults to feed_title)
        language          – BCP-47 language tag (default "en")
        item_guid_is_permalink – set guid isPermaLink="true" (default False)
        min_item_count    - minimum extracted items required to write a feed
                            (default 1)
        min_item_ratio_vs_previous - if a previous feed exists, require at
                            least ceil(previous_count * ratio) items
                            (default 0.6)
    """

    # Feed metadata
    feed_title: Optional[str] = None
    source_url: Optional[str] = None
    feed_link: Optional[str] = None
    feed_description: Optional[str] = None
    language: str = "en"

    # Item selectors
    item_container_selector: Optional[str] = None
    item_title_selector: Optional[str] = None
    item_link_selector: Optional[str] = None
    item_date_selector: Optional[str] = None
    item_description_selector: Optional[str] = None

    # Link handling
    item_guid_is_permalink: bool = False

    # Validation guardrails
    min_item_count: int = 1
    min_item_ratio_vs_previous: float = 0.6

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
        self._validate_spider_config()

        if response.status != 200:
            raise RuntimeError(
                f"Source URL returned HTTP {response.status}: {response.url}"
            )

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

        skipped_count = container_count - item_count
        if skipped_count:
            self.logger.warning(
                "Skipped %s/%s matched containers due to missing required fields",
                skipped_count,
                container_count,
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
            fe.id(item["link"])

            if item.get("description"):
                fe.description(item["description"])
            if item.get("date"):
                fe.pubDate(item["date"])

        os.makedirs("feeds", exist_ok=True)
        feed_path = f"feeds/{self.name}.xml"
        fg.rss_file(feed_path, pretty=True)
        self.logger.info("Feed written to %s", feed_path)

    def _validate_spider_config(self):
        required_fields = {
            "name": self.name,
            "feed_title": self.feed_title,
            "source_url": self.source_url,
            "item_container_selector": self.item_container_selector,
            "item_title_selector": self.item_title_selector,
            "item_link_selector": self.item_link_selector,
        }
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
                date = dateparser.parse(
                    date_str,
                    settings={
                        "RETURN_AS_TIMEZONE_AWARE": True,
                        "PREFER_DAY_OF_MONTH": "first",
                    },
                )

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

