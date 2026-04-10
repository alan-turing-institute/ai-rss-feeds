"""Run all spiders and write feeds to feeds/."""

import argparse

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from ai_rss_feeds.spiders.aisi import AISIBlogSpider
from ai_rss_feeds.spiders.allenai import AllenAINewsSpider
from ai_rss_feeds.spiders.anthropic import AnthropicNewsSpider
from ai_rss_feeds.spiders.tldr_ai import TLDRAIArchivesSpider


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

    spider_classes = [
        AnthropicNewsSpider,
        AllenAINewsSpider,
        AISIBlogSpider,
        TLDRAIArchivesSpider,
    ]

    for spider_cls in spider_classes:
        crawler = process.create_crawler(spider_cls)
        crawler.signals.connect(on_spider_error, signal=signals.spider_error)
        process.crawl(crawler)

    process.start()

    if spider_errors:
        for spider_name, error in spider_errors:
            print(f"ERROR in spider '{spider_name}': {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
