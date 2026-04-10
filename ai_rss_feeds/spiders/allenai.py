"""Allen Institute for AI (Ai2) News spider.

Source: https://allenai.org/news

Page structure (simplified):
    <div class="... grid-tc_repeat(3,_1fr) ...">  ← 3-column news grid
      <div class="... grid-tr_subgrid ...">        ← one card per item
        <div>…image…</div>
        <h2>
          <span class="...wideCardEyebrow">March 2026</span>
          <span class="sr_true"> - </span>
          Title text                               ← direct text node of <h2>
        </h2>
        <div>…description paragraph…</div>
        <div>
          <a href="/blog/<slug>">Read post</a>
        </div>
      </div>
    </div>

Note: dates are month+year only (e.g. "March 2026"); dateparser maps these to
the first of that month.
"""

from .base import BaseFeedSpider


class AllenAINewsSpider(BaseFeedSpider):
    name = "allenai-news"
    feed_title = "Ai2 News"
    source_url = "https://allenai.org/news"

    # Each card is a direct child div of the 3-column grid container
    item_container_selector = "div[class*='grid-tc_repeat'] > div"
    item_link_selector = "a[href^='/blog/']::attr(href)"
    # h2::text returns the direct text nodes of <h2>, which is the title;
    # the date lives in a child <span> and is NOT included by ::text
    item_title_selector = "h2::text"
    item_date_selector = "h2 span:first-child::text"
    item_description_selector = "div > p::text"
