BOT_NAME = "ai_rss_feeds"

SPIDER_MODULES = ["ai_rss_feeds.spiders"]
NEWSPIDER_MODULE = "ai_rss_feeds.spiders"

# Enable HTTP caching unconditionally; delete .scrapy/httpcache to refresh
HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = ".scrapy/httpcache"
HTTPCACHE_EXPIRATION_SECS = 0  # Never expire automatically

LOG_LEVEL = "INFO"
