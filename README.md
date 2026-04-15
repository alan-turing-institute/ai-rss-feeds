# AI RSS Feeds

This project generates RSS 2.0 feeds for AI news/blog sites that do not publish feeds directly.

## Feeds

| Name | File |
|---|---|
| [AISI Blog (AI Security Institute)](https://www.aisi.gov.uk/blog) | [feeds/aisi-blog.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/aisi-blog.xml) |
| [Ai2 News (Allen Institute for AI)](https://allenai.org/news) | [feeds/allenai-news.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/allenai-news.xml) |
| [Claude Blog](https://claude.com/blog) | [feeds/claude-blog.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/claude-blog.xml) |
| [Cohere Blog](https://cohere.com/blog) | [feeds/cohere-blog.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/cohere-blog.xml) |
| [Mila News (Quebec AI Institute)](https://mila.quebec/en/news) | [feeds/mila-news.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/mila-news.xml) |
| [Anthropic News](https://www.anthropic.com/news) | [feeds/anthropic-news.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/anthropic-news.xml) |
| [Anthropic Research](https://www.anthropic.com/research) | [feeds/anthropic-research.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/anthropic-research.xml) |
| [Mistral News](https://mistral.ai/news) | [feeds/mistral-news.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/mistral-news.xml) |
| [The Batch](https://www.deeplearning.ai/the-batch/) | [feeds/the-batch.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/the-batch.xml) |
| [TLDR AI](https://tldr.tech/ai/archives) | [feeds/tldr-ai.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/tldr-ai.xml) |
| [Turing Blog (Alan Turing Institute)](https://www.turing.ac.uk/blog) | [feeds/turing-blog.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/turing-blog.xml) |
| [Turing News (Alan Turing Institute)](https://www.turing.ac.uk/news) | [feeds/turing-news.xml](https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/turing-news.xml) |

## Generate Feeds

Use the generator script:

```bash
uv run python generate_feeds.py
```

Generated feed files are written to `./feeds`.

By default all feeds are generated, but you can specify which to generate:

```bash
uv run python generate_feeds.py aisi-blog allenai-news
```

Options:

- `--no-cache`: disable Scrapy HTTP cache for that run
- `--skip-unchanged`: skip writing a feed file if its only change would be `lastBuildDate`

The scheduled GitHub Actions workflow uses `--skip-unchanged`, so it does not create a commit when feeds are otherwise unchanged.

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
2. Set required fields for HTML feeds:
	- `feed_title`
	- `source_url`
	- `item_container_selector`
	- `item_title_selector`
	- `item_link_selector`
3. For Next.js feeds, set:
	- `format = "nextjs"`
	- `item_container_selector` as a JSONPath query that returns item objects (for example `$..initialPosts[*]`)
	- `item_title_selector`, `item_link_selector`, and optional `item_date_selector` / `item_description_selector` as JSONPath queries scoped to each item
4. Set optional fields as needed:
	- `item_date_selector`, `item_date_regex`, `item_description_selector`, `feed_description`, `language`
	- `item_guid_is_permalink`, `min_item_count`, `min_item_ratio_vs_previous`
	- save a local source snapshot in `snapshots/` and develop selectors against that copy
	- comments above the feed table to keep source/structure notes alongside selectors
5. Add the new feed entry to the table above, keeping it sorted by name.
6. Run `uv run python generate_feeds.py` and verify output in `feeds/`.
