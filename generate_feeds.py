"""Run all spiders and write feeds to feeds/."""

import argparse

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from src.feed_config import list_feed_keys
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

    settings = get_project_settings()
    if args.no_cache:
        settings.set("HTTPCACHE_ENABLED", False, priority="cmdline")

    process = CrawlerProcess(settings)

    spider_errors = []

    def on_spider_error(failure, response, spider):
        spider_errors.append((spider.name, str(failure.value)))

    for feed_key in selected_feed_keys:
        crawler = process.create_crawler(FeedSpider)
        crawler.signals.connect(on_spider_error, signal=signals.spider_error)
        process.crawl(crawler, feed_key=feed_key, skip_unchanged=args.skip_unchanged)

    process.start()

    if spider_errors:
        for spider_name, error in spider_errors:
            print(f"ERROR in spider '{spider_name}': {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
