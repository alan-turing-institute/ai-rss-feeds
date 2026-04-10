"""Run all spiders and write feeds to feeds/."""

import argparse

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from src.feed_config import list_feed_keys
from src.spiders.feed import FeedSpider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all feed spiders.")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable Scrapy HTTP cache for this run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_project_settings()
    if args.no_cache:
        settings.set("HTTPCACHE_ENABLED", False, priority="cmdline")

    process = CrawlerProcess(settings)

    spider_errors = []

    def on_spider_error(failure, response, spider):
        spider_errors.append((spider.name, str(failure.value)))

    for feed_key in list_feed_keys():
        crawler = process.create_crawler(FeedSpider)
        crawler.signals.connect(on_spider_error, signal=signals.spider_error)
        process.crawl(crawler, feed_key=feed_key)

    process.start()

    if spider_errors:
        for spider_name, error in spider_errors:
            print(f"ERROR in spider '{spider_name}': {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
