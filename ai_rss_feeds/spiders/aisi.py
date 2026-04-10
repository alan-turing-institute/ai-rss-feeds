"""UK AI Security Institute (AISI) Blog spider.

Source: https://www.aisi.gov.uk/blog

Page structure (simplified):
    <div role="listitem" class="work-card-wrapper w-dyn-item">
      <div class="card in-grid">
        <a href="/blog/<slug>" class="... w-inline-block">
          <h3 class="text-size-lg">Title</h3>
        </a>
        <div class="flex_tags ...">
          …
          <p fs-list-field="date" …>Mar 31, 2026</p>
        </div>
        <div class="flex-grow">
          <p fs-list-field="description" …>Description text</p>
        </div>
      </div>
    </div>
"""

from .base import BaseFeedSpider


class AISIBlogSpider(BaseFeedSpider):
    name = "aisi-blog"
    feed_title = "AISI Blog"
    feed_description = "Updates on AISI's work – AI Security Institute"
    source_url = "https://www.aisi.gov.uk/blog"

    item_container_selector = "div.work-card-wrapper"
    item_link_selector = "a.w-inline-block[href^='/blog/']::attr(href)"
    item_title_selector = "h3::text"
    item_date_selector = "p[fs-list-field='date']::text"
    item_description_selector = "p[fs-list-field='description']::text"
