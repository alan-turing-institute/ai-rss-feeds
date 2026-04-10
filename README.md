# AI RSS Feeds

This project generates RSS 2.0 feeds for AI news/blog sites that do not publish feeds directly.

## Feeds

| Name | File |
|---|---|
| Ai2 News | `feeds/allenai-news.xml` |
| AISI Blog | `feeds/aisi-blog.xml` |
| Anthropic News | `feeds/anthropic-news.xml` |

## Generate Feeds

Run all feeds:

```bash
uv run python generate_feeds.py
```

Run a single feed spider:

```bash
uv run scrapy crawl anthropic-news
uv run scrapy crawl allenai-news
uv run scrapy crawl aisi-blog
```

Generated feed files are written to `./feeds`.

## HTTP Cache

Scrapy HTTP cache is always enabled in `ai_rss_feeds/settings.py`.

To refresh cached source pages, delete:

```bash
rm -rf .scrapy/httpcache
```

## Add A New Feed

1. Add a new spider class in `ai_rss_feeds/spiders/` that inherits from `BaseFeedSpider`.
2. Set required metadata fields:
	- `name`
	- `feed_title`
	- `source_url`
3. Set selectors for items:
	- `item_container_selector`
	- `item_title_selector`
	- `item_link_selector`
	- optionally `item_date_selector`, `item_description_selector`, `language`, etc.
4. Add the spider class to `generate_feeds.py`.
5. Add the new feed entry to the table above, keeping it sorted by name.
6. Run `uv run python generate_feeds.py` and verify output in `feeds/`.
