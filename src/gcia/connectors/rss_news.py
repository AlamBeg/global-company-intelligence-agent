from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Iterable

from gcia.schemas.discussion import RawRecord


class RssNewsConnector:
    """Minimal example connector for public RSS news feeds.

    This is a reference implementation, not production-ready: real
    connectors must additionally track rate limits, licensing, robots/access
    rules, and health status per docs/SOURCE_CONNECTORS.md. It exists here to
    prove the Connector -> RawRecord -> NormalizationAgent path end to end.
    """

    source_type = "news"
    platform = "rss"

    def __init__(self, feed_url: str):
        self.feed_url = feed_url

    def collect(self, query: str | None = None, since: datetime | None = None) -> Iterable[RawRecord]:
        with urllib.request.urlopen(self.feed_url, timeout=10) as response:
            raw_xml = response.read()
        root = ET.fromstring(raw_xml)
        collected_at = datetime.now(timezone.utc)

        for item in root.findall(".//item"):
            link = item.findtext("link") or None
            guid = item.findtext("guid") or link
            if guid is None:
                continue  # no connector-owned identifier: skip rather than invent one (FR-005)
            yield RawRecord(
                platform=self.platform,
                source_native_id=guid,
                original_url=link,
                title=item.findtext("title"),
                content=item.findtext("description") or "",
                collected_at=collected_at,
                raw_payload={child.tag: (child.text or "") for child in item},
            )
