"""Run all spiders and write feeds to feeds/."""

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from ai_rss_feeds.spiders.aisi import AISIBlogSpider
from ai_rss_feeds.spiders.allenai import AllenAINewsSpider
from ai_rss_feeds.spiders.anthropic import AnthropicNewsSpider


def main():
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(AnthropicNewsSpider)
    process.crawl(AllenAINewsSpider)
    process.crawl(AISIBlogSpider)
    process.start()


if __name__ == "__main__":
    main()
