"""Run all spiders and write feeds to feeds/."""

import argparse

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from ai_rss_feeds.spiders.aisi import AISIBlogSpider
from ai_rss_feeds.spiders.allenai import AllenAINewsSpider
from ai_rss_feeds.spiders.anthropic import AnthropicNewsSpider


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
    process.crawl(AnthropicNewsSpider)
    process.crawl(AllenAINewsSpider)
    process.crawl(AISIBlogSpider)
    process.start()


if __name__ == "__main__":
    main()
