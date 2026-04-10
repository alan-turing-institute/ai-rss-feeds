# AI RSS Feeds

This project generates RSS 2.0 feeds for AI news/blog sites that do not publish feeds directly.

## Feeds

| Name | File |
|---|---|
| [Ai2 News](https://allenai.org/news) | `feeds/allenai-news.xml` |
| [AISI Blog](https://www.aisi.gov.uk/blog) | `feeds/aisi-blog.xml` |
| [Anthropic News](https://www.anthropic.com/news) | `feeds/anthropic-news.xml` |
| [Anthropic Research](https://www.anthropic.com/research) | `feeds/anthropic-research.xml` |
| [Claude Blog](https://claude.com/blog) | `feeds/claude-blog.xml` |
| [TLDR AI](https://tldr.tech/ai/archives) | `feeds/tldr-ai.xml` |

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
uv run scrapy crawl feed -a feed_key=anthropic-news
uv run scrapy crawl feed -a feed_key=anthropic-research
uv run scrapy crawl feed -a feed_key=allenai-news
uv run scrapy crawl feed -a feed_key=aisi-blog
uv run scrapy crawl feed -a feed_key=claude-blog
uv run scrapy crawl feed -a feed_key=tldr-ai
```

Run a single feed spider with HTTP cache disabled for that run:

```bash
uv run scrapy crawl feed -a feed_key=anthropic-news -s HTTPCACHE_ENABLED=False
uv run scrapy crawl feed -a feed_key=anthropic-research -s HTTPCACHE_ENABLED=False
uv run scrapy crawl feed -a feed_key=allenai-news -s HTTPCACHE_ENABLED=False
uv run scrapy crawl feed -a feed_key=aisi-blog -s HTTPCACHE_ENABLED=False
uv run scrapy crawl feed -a feed_key=claude-blog -s HTTPCACHE_ENABLED=False
uv run scrapy crawl feed -a feed_key=tldr-ai -s HTTPCACHE_ENABLED=False
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

Scrapy HTTP cache is enabled by default in `src/settings.py`.
Use `uv run python generate_feeds.py --no-cache` to disable cache for a single run.

To refresh cached source pages, delete:

```bash
rm -rf .scrapy/httpcache
```

## Add A New Feed

1. Add a new `[feeds.<feed-key>]` table in `feeds.toml`.
2. Set required fields:
	- `feed_title`
	- `source_url`
	- `item_container_selector`
	- `item_title_selector`
	- `item_link_selector`
3. Set optional fields as needed:
	- `item_date_selector`, `item_description_selector`, `feed_description`, `language`
	- `item_guid_is_permalink`, `min_item_count`, `min_item_ratio_vs_previous`
	- `user_agent` for a per-feed request header override
	- comments above the feed table to keep source/structure notes alongside selectors
4. Add the new feed entry to the table above, keeping it sorted by name.
5. Run `uv run python generate_feeds.py` and verify output in `feeds/`.
