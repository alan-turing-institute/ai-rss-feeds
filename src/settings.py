BOT_NAME = "src"

SPIDER_MODULES = ["src.spiders"]
NEWSPIDER_MODULE = "src.spiders"

# Enable HTTP caching unconditionally; delete .scrapy/httpcache to refresh
HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_EXPIRATION_SECS = 0  # Never expire automatically

# Global user agent for all requests
USER_AGENT = "ai-rss-feeds-bot/1.0 (+https://github.com/alan-turing-institute/ai-rss-feeds)"

LOG_LEVEL = "INFO"
