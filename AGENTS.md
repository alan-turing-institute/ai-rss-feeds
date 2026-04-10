## Overview
- This is a collection of RSS 2.0 feeds for AI news and blog sites which don't provide RSS feeds themselves.
- Tech stack:
    - `uv` for project management - use it to manage packages and run commands in the project.
    - `scrapy` to scrape the sites.
    - `feedgen` to generate RSS feeds.
    - `dateparser` to parse dates.
- Document the feeds in a table in the README, giving the name (e.g. Anthropic News) and filename (e.g. `feeds/anthropic-news.xml`). Keep it sorted by name.
- The README should also document any commands `uv run ...` to generate feeds and instructions for adding new feeds.
- Refer to the README as well as this AGENTS file when you perform a task.

## Scraping with scrapy
- Enable HTTP cacheing unconditionally. I will delete the cache now and then to keep things fresh.
- There is a separate scraper class for each feed, but they all inherit from a common base class which has the logic to cover most common cases.
- The specific classes just need to define:
  - required fields like `title` and `source_url`,
  - optional fields like `language`,
  - fields like `item_container_selector` (CSS selector for the container for each item)
  - fields like `item_title_selector`, `item_link_selector` (CSS selectors for the title or link for a specific item, scoped to the container for the item, these can be scrapy's extended selectors with the suffixes like `::text` and `::attr(href)`)
  - other fields like `item_guid_is_link` (use the link as the guid), `item_guid_is_permalink` (set the guid to be a permalink), `item_date_regex` (regex to extract the date portion, such as if `item_link_selector` is something like `a::attr(href)` and the date needs to be extracted from the URL) and more that may be required as we go along.
- These mostly default to `None` and if left as `None` then the corresponding field in the feed or item is not set.
- Be lenient in what selectors can return. For example `item_link_selector` can return either text (the URL) or an HTML node (in which case its `href` attr is taken).
- Don't follow any links (to articles or to later pages of links), just use the information on the source page.
- Don't repeatedly curl a page when developing feeds - put a copy into `./snapshots` and refer to that.

## Feed generation
- Each site will correspond to one feed, e.g. the Anthropic News site will become a `anthropic-news.xml` feed.
- Feeds are put into `./feeds`.
- Look at existing spiders (`ai_rss_feeds/spiders`) for consistency.
- Use selectors that are likely to be stable over time.

## Regeneration
- Currently this will be run manually.
- Later it will be run in a cron job.