# AI RSS Feeds

This project generates RSS 2.0 feeds for AI news/blog sites that do not publish feeds directly.

## Feeds

| Name | File |
|---|---|
| Ai2 News | `feeds/allenai-news.xml` |
| AISI Blog | `feeds/aisi-blog.xml` |
| Anthropic News | `feeds/anthropic-news.xml` |
| TLDR AI | `feeds/tldr-ai.xml` |

## Generate Feeds

Run all feeds:

```bash
uv run python generate_feeds.py
```

Run all feeds with HTTP cache disabled for that run:

```bash
uv run python generate_feeds.py --no-cache
```

Run a single feed spider:

```bash
uv run scrapy crawl anthropic-news
uv run scrapy crawl allenai-news
uv run scrapy crawl aisi-blog
uv run scrapy crawl tldr-ai
```

Run a single feed spider with HTTP cache disabled for that run:

```bash
uv run scrapy crawl anthropic-news -s HTTPCACHE_ENABLED=False
uv run scrapy crawl allenai-news -s HTTPCACHE_ENABLED=False
uv run scrapy crawl aisi-blog -s HTTPCACHE_ENABLED=False
uv run scrapy crawl tldr-ai -s HTTPCACHE_ENABLED=False
```

Generated feed files are written to `./feeds`.

## Validation and Failure Behavior

Feed generation is fail-fast.

- If the source URL does not return HTTP 200, that spider raises an error.
- If `item_container_selector` matches nothing, that spider raises an error.
- If too few items are extracted, that spider raises an error.

By default, each spider enforces:

- `min_item_count = 1`
- `min_item_ratio_vs_previous = 0.6` when an existing `feeds/<name>.xml` file is present

This prevents silently writing empty or unexpectedly tiny feeds when page markup changes.
`uv run python generate_feeds.py` exits with a non-zero status if any spider errors.

## HTTP Cache

Scrapy HTTP cache is enabled by default in `ai_rss_feeds/settings.py`.
Use `uv run python generate_feeds.py --no-cache` to disable cache for a single run.

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
	- optionally tighten validation with `min_item_count` and/or `min_item_ratio_vs_previous`
4. Add the spider class to `generate_feeds.py`.
5. Add the new feed entry to the table above, keeping it sorted by name.
6. Run `uv run python generate_feeds.py` and verify output in `feeds/`.
