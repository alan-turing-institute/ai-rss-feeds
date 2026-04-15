"""Generate an OPML subscription list from feeds.toml."""

from pathlib import Path
import xml.etree.ElementTree as ET

from src.feed_config import load_all_feeds


REPO_RAW_BASE_URL = (
    "https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main"
)
OPML_PATH = Path(__file__).resolve().parent / "feeds.opml"


def build_opml_tree() -> ET.ElementTree:
    feeds = load_all_feeds()
    root = ET.Element("opml", version="1.0")

    head = ET.SubElement(root, "head")
    ET.SubElement(head, "title").text = "AI RSS Feeds"

    body = ET.SubElement(root, "body")

    for feed_key, config in sorted(feeds.items(), key=lambda item: (item[1]["feed_title"].lower(), item[0])):
        feed_title = config["feed_title"]
        feed_url = f"{REPO_RAW_BASE_URL}/feeds/{feed_key}.xml"
        source_url = config["source_url"]
        ET.SubElement(
            body,
            "outline",
            {
                "type": "rss",
                "text": feed_title,
                "title": feed_title,
                "xmlUrl": feed_url,
                "htmlUrl": source_url,
            },
        )

    ET.indent(root, space="  ")
    return ET.ElementTree(root)


def main() -> None:
    tree = build_opml_tree()
    tree.write(OPML_PATH, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()