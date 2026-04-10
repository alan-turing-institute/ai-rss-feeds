"""Anthropic News spider.

Source: https://www.anthropic.com/news

Page structure (simplified):
    <ul>
      <li>
        <a href="/news/<slug>">
          <div>
            <time>Apr 6, 2026</time>
            <span>Category</span>
          </div>
          <span>Title text</span>         ← direct child span of <a>
        </a>
      </li>
    </ul>
"""

from .base import BaseFeedSpider


class AnthropicNewsSpider(BaseFeedSpider):
    name = "anthropic-news"
    feed_title = "Anthropic News"
    source_url = "https://www.anthropic.com/news"

    # Each news item lives in a <li>; nav/footer <li>s lack a /news/<slug> link
    # so they produce no match on item_link_selector and are skipped.
    item_container_selector = "ul li"
    item_link_selector = "a[href^='/news/']::attr(href)"
    item_title_selector = "a[href^='/news/'] > span:last-child::text"
    item_date_selector = "a[href^='/news/'] time::text"

    item_link_base_url = "https://www.anthropic.com"
