"""Claude Blog spider.

Source: https://claude.com/blog

Page structure (simplified):
    <div role="listitem" class="marquee_cms_blog_list_item w-dyn-item">
      <div class="marquee_cms_blog_list_item_content">
        <h2>Title</h2>
        <div class="u-text-style-caption u-foreground-tertiary">April 8, 2026</div>
      </div>
      <div class="clickable_wrap u-cover-absolute">
        <a href="/blog/<slug>" class="clickable_link ...">Read more</a>
      </div>
    </div>
"""

from .base import BaseFeedSpider


class ClaudeBlogSpider(BaseFeedSpider):
    name = "claude-blog"
    feed_title = "Claude Blog"
    source_url = "https://claude.com/blog"

    item_container_selector = "div.marquee_cms_blog_list_item.w-dyn-item"
    item_title_selector = "h2::text"
    item_link_selector = "a[href^='/blog/']::attr(href)"
    item_date_selector = "div.u-text-style-caption::text"
