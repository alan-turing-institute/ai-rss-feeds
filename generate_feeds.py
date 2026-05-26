"""Generate RSS feeds by scraping configured sources and writing XML to feeds/.

Reads feed definitions from feeds.toml and runs a Scrapy spider for each one.
Supports selective runs by passing feed keys as positional arguments; defaults
to all configured feeds. HTTP responses are cached by default (see scrapy.cfg).

Usage:
    python generate_feeds.py                     # run all feeds
    python generate_feeds.py anthropic-news      # run one feed
    python generate_feeds.py --no-cache          # bypass HTTP cache
    python generate_feeds.py --skip-unchanged    # skip writing if only lastBuildDate changed
"""

import argparse

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from src.feed_config import list_feed_keys, load_all_feeds
from src.spiders.feed import FeedSpider


def parse_args() -> argparse.Namespace:
    feed_keys = list_feed_keys()

    parser = argparse.ArgumentParser(
        description=(
            "Run feed spiders. If no feed keys are provided, all configured feeds are run."
        )
    )
    parser.add_argument(
        "feed_keys",
        nargs="*",
        choices=feed_keys,
        metavar="feed_key",
        help="Optional feed keys to run. Defaults to all configured feeds.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable Scrapy HTTP cache for this run.",
    )
    parser.add_argument(
        "--skip-unchanged",
        action="store_true",
        help="Skip writing a feed file if the only change is lastBuildDate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected_feed_keys = args.feed_keys or list_feed_keys()

    all_feeds = load_all_feeds()
    broken_feed_keys = {k for k, v in all_feeds.items() if v.get("broken")}

    settings = get_project_settings()
    if args.no_cache:
        settings.set("HTTPCACHE_ENABLED", False, priority="cmdline")

    process = CrawlerProcess(settings)

    spider_errors = {}

    def on_spider_error(failure, response, spider):
        spider_errors[spider.name] = str(failure.value)

    for feed_key in selected_feed_keys:
        crawler = process.create_crawler(FeedSpider)
        crawler.signals.connect(on_spider_error, signal=signals.spider_error)
        process.crawl(crawler, feed_key=feed_key, skip_unchanged=args.skip_unchanged)

    process.start()

    has_real_errors = False

    for feed_key in selected_feed_keys:
        if feed_key in broken_feed_keys:
            if feed_key in spider_errors:
                print(f"BROKEN: {feed_key}: {spider_errors[feed_key]}")
            else:
                print(f"ERROR: {feed_key}: broken feed succeeded — remove 'broken=true' from feeds.toml")
                has_real_errors = True
        elif feed_key in spider_errors:
            print(f"ERROR: {feed_key}: {spider_errors[feed_key]}")
            has_real_errors = True

    if has_real_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
