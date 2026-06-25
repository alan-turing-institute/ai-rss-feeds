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
- Enable HTTP caching unconditionally. I will delete the cache now and then to keep things fresh.
- Use a single configurable spider class, with per-feed configuration in `feeds.toml`.
- Each feed entry in TOML should define:
  - required fields like `feed_title`, `source_url`, `item_container_selector`, `item_title_selector`, and `item_link_selector`,
  - optional fields like `feed_link`, `feed_description`, and `language`,
  - fields like `item_container_selector` (CSS selector for the container for each item)
  - fields like `item_title_selector`, `item_link_selector` (CSS selectors for the title or link for a specific item, scoped to the container for the item, these can be scrapy's extended selectors with the suffixes like `::text` and `::attr(href)`)
  - other supported fields like `item_date_selector`, `item_description_selector`, `item_guid_is_permalink`, `min_item_count`, and `min_item_ratio_vs_previous`.
- These mostly default to `None` and if left as `None` then the corresponding field in the feed or item is not set.
- Be lenient in what selectors can return. For example `item_link_selector` can return either text (the URL) or an HTML node (in which case its `href` attr is taken).
- Don't follow any links (to articles or to later pages of links), just use the information on the source page.
- Don't repeatedly curl a page when developing feeds - put a copy into `./snapshots` and refer to that.
- To refresh a snapshot directly, use e.g. `curl -f https://www.anthropic.com/news -o snapshots/anthropic-news.html`.
- If a new feed can't be scraped with the existing setup, suggest how to proceed and we can discuss before implementing new scraping methods.
- If the feed uses nextjs, you can extract the nextjs data like `uv run python extract_nextjs.py snapshots/cohere-blog.html >snapshots/cohere-blog.nextjs.json`.
- You can find where items are in nextjs like `uv run python json_grep.py snapshots/cohere-blog.nextjs.json "Part of the title"` if the user gives example titles (ask for some).

## Feed generation
- Each site will correspond to one feed, e.g. the Anthropic News site will become a `anthropic-news.xml` feed.
- Feeds are put into `./feeds`.
- Look at existing feeds (`feeds.toml`) for consistency.
- Use selectors that are likely to be stable over time.
- When you add a new feed, run `uv run python generate_opml.py` to regenerate the OPML list.

## Broken feeds
- If a feed stops working, it can be marked `broken = true` in `feeds.toml`. This will stop a known problem from failing the whole run, and will flag when it starts working again.
- To fix a feed:
  - Grab a new snapshot (as above).
  - If it uses nextjs, extract the data (as above).
  - Read the existing feed in `feeds.toml`.
  - Compare it to the new snapshots and fix the feed.
  - Remove `broken = true`.
- News pages sometimes have featured articles shown differently from the main list, ensure you get them all. It can help if the user supplies the titles for a selection of articles (featured and not), so you can find them more easily in the HTML.

## Regeneration
- There is a github workflow (`.github/workflows/generate-feeds.yml`) that runs every 3 hours.
- Can also trigger it manually.
