from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urlsplit

from gcia.schemas.discussion import RawRecord


class RedditPublicConnector:
    """Reference connector for Reddit's public, unauthenticated JSON
    listings (e.g. https://www.reddit.com/r/<subreddit>/new.json).

    Not production-ready: real deployment should use Reddit's official API
    with proper authentication, respect its rate limits and API terms, and
    track connector health per docs/SOURCE_CONNECTORS.md. This exists to
    prove the Connector protocol generalizes beyond RSS with a second,
    structurally different source (JSON listing vs. XML feed, native engagement
    metrics, native author handles).
    """

    source_type = "social"
    platform = "reddit"

    def __init__(self, listing_url: str, limit: int = 25):
        self.listing_url = listing_url
        self.limit = limit

    def collect(self, query: str | None = None, since: datetime | None = None) -> Iterable[RawRecord]:
        # Only append Reddit's listing query params over http(s) - a file://
        # fixture URL (used in tests) has no such API and must be read as-is.
        if urlsplit(self.listing_url).scheme in ("http", "https"):
            url = f"{self.listing_url}?limit={self.limit}&raw_json=1"
        else:
            url = self.listing_url
        request = urllib.request.Request(url, headers={"User-Agent": "gcia-reference-connector/0.1"})
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read())
        collected_at = datetime.now(timezone.utc)

        for child in payload.get("data", {}).get("children", []):
            post = child.get("data", {})
            post_id = post.get("id")
            if not post_id:
                continue  # no connector-owned identifier: skip rather than invent one (FR-005)
            permalink = post.get("permalink")
            original_url = f"https://www.reddit.com{permalink}" if permalink else None
            created_utc = post.get("created_utc")
            published_at = (
                datetime.fromtimestamp(created_utc, tz=timezone.utc) if created_utc else None
            )
            yield RawRecord(
                platform=self.platform,
                source_native_id=post_id,
                original_url=original_url,
                author_public_name=post.get("author"),
                published_at=published_at,
                collected_at=collected_at,
                title=post.get("title"),
                content=post.get("selftext") or post.get("title") or "",
                engagement={
                    "score": int(post.get("score") or 0),
                    "num_comments": int(post.get("num_comments") or 0),
                },
                raw_payload={k: v for k, v in post.items() if isinstance(v, (str, int, float, bool))},
            )
