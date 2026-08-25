"""Downloader middleware for feeds behind browser-fingerprint bot protection.

Some sources (e.g. x.ai) sit behind Cloudflare bot management, which scores the
TLS ClientHello and HTTP/2 SETTINGS fingerprint rather than request headers.
Scrapy uses Python's TLS stack, so those requests are blocked with HTTP 403 no
matter which headers are sent. `curl_cffi` reproduces a real browser's
fingerprint, so feeds can opt in via `impersonate = "chrome"` in feeds.toml.

Registered *after* HttpCacheMiddleware (order 900) so cached responses are still
served without hitting the network; only cache misses reach curl_cffi.
"""

from scrapy.http import HtmlResponse


class ImpersonateDownloaderMiddleware:
    """Fetch requests carrying `meta['impersonate']` via curl_cffi."""

    def process_request(self, request, spider):
        target = request.meta.get("impersonate")
        if not target:
            return None

        # Imported lazily so the dependency is only needed by feeds that use it.
        from curl_cffi import requests as curl_requests

        response = curl_requests.get(
            request.url,
            impersonate=target,
            timeout=30,
        )

        return HtmlResponse(
            url=str(response.url),
            status=response.status_code,
            body=response.content,
            encoding=response.encoding or "utf-8",
            request=request,
        )
