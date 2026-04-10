"""Anthropic Research spider.

Source: https://www.anthropic.com/research

Page structure (simplified):
    <a href="/research/<slug>" class="...listItem">
      <div class="...meta">
        <time class="...date">Apr 9, 2026</time>
        <span class="...subject">Policy</span>
      </div>
      <span class="...title">Trustworthy agents in practice</span>
    </a>
"""

from .base import BaseFeedSpider


class AnthropicResearchSpider(BaseFeedSpider):
    name = "anthropic-research"
    feed_title = "Anthropic Research"
    source_url = "https://www.anthropic.com/research"

    item_container_selector = "a[class*=PublicationList][class*=listItem]"
    item_link_selector = "::attr(href)"
    item_title_selector = "span[class*=title]::text"
    item_date_selector = "time::text"
