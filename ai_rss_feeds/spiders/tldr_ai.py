"""TLDR AI Archives spider.

Source: https://tldr.tech/ai/archives

Page structure (simplified):
    <a href="/ai/2026-04-08">
      <div class="mb-4">Issue subject line</div>
    </a>

The page also contains other links, so we scope items to dated archive links.
"""

from .base import BaseFeedSpider


class TLDRAIArchivesSpider(BaseFeedSpider):
    name = "tldr-ai"
    feed_title = "TLDR AI"
    source_url = "https://tldr.tech/ai/archives"

    custom_settings = {
        "USER_AGENT": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_0) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
        )
    }

    # Each archive item is a dated link like /ai/YYYY-MM-DD.
    item_container_selector = "a[href^='/ai/20']"
    item_link_selector = "::attr(href)"
    item_title_selector = "div::text"
