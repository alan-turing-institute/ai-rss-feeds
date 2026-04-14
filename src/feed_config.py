"""Load and validate feed definitions from feeds.toml."""

from pathlib import Path
import tomllib


FEEDS_TOML_PATH = Path(__file__).resolve().parents[1] / "feeds.toml"


KNOWN_FEED_FIELDS = {
    "feed_title",
    "source_url",
    "feed_link",
    "feed_description",
    "language",
    "item_container_selector",
    "item_title_selector",
    "item_link_selector",
    "item_date_selector",
    "item_description_selector",
    "item_guid_is_permalink",
    "min_item_count",
    "min_item_ratio_vs_previous",
}


def load_all_feeds() -> dict[str, dict]:
    with FEEDS_TOML_PATH.open("rb") as f:
        data = tomllib.load(f)

    feeds = data.get("feeds")
    if not isinstance(feeds, dict) or not feeds:
        raise RuntimeError("feeds.toml must contain a non-empty [feeds] table")

    for feed_key, config in feeds.items():
        if not isinstance(config, dict):
            raise RuntimeError(f"Feed '{feed_key}' must be a TOML table")

        unknown = sorted(set(config) - KNOWN_FEED_FIELDS)
        if unknown:
            unknown_str = ", ".join(unknown)
            raise RuntimeError(f"Feed '{feed_key}' has unknown fields: {unknown_str}")

    return feeds


def load_feed(feed_key: str) -> dict:
    feeds = load_all_feeds()
    if feed_key not in feeds:
        known = ", ".join(sorted(feeds))
        raise RuntimeError(f"Unknown feed_key '{feed_key}'. Known feeds: {known}")
    return feeds[feed_key]


def list_feed_keys() -> list[str]:
    return sorted(load_all_feeds().keys())
