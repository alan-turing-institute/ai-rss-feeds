"""Base spider class — subclasses define selectors and feed metadata."""

import os

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
        item_link_base_url – prepended to relative links (default: origin of source_url)
        item_guid_is_permalink – set guid isPermaLink="true" (default False)
    """

    # Feed metadata
    feed_title: str = None
    source_url: str = None
    feed_link: str = None
    feed_description: str = None
    language: str = "en"

    # Item selectors
    item_container_selector: str = None
    item_title_selector: str = None
    item_link_selector: str = None
    item_date_selector: str = None
    item_description_selector: str = None

    # Link handling
    item_link_base_url: str = None
    item_guid_is_permalink: bool = False

    @property
    def start_urls(self):
        return [self.source_url]

    def parse(self, response):
        fg = FeedGenerator()
        fg.id(self.source_url)
        fg.title(self.feed_title)
        link = self.feed_link or self.source_url
        fg.link(href=link, rel="alternate")
        fg.description(self.feed_description or self.feed_title)
        if self.language:
            fg.language(self.language)

        for container in response.css(self.item_container_selector):
            item = self._extract_item(container, response)
            if item is None:
                continue

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

        # Make absolute
        if link_val.startswith("/"):
            base = self.item_link_base_url or self._origin(response.url)
            link_val = base + link_val

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

    @staticmethod
    def _origin(url: str) -> str:
        """Return scheme://host from a URL."""
        parts = url.split("/")
        return f"{parts[0]}//{parts[2]}"
