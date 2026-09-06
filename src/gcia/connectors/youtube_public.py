from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Iterable

from gcia.schemas.discussion import RawRecord

_API_BASE = "https://www.googleapis.com/youtube/v3"


def _parse_youtube_timestamp(raw: str | None) -> datetime | None:
    """YouTube timestamps are RFC 3339 (e.g. "2026-09-04T12:34:56Z")."""
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


class YouTubeConnector:
    """Reference connector for the YouTube Data API v3 (public-data API key,
    no OAuth): searches public videos for a query, then reads each video's
    public top-level comments as individual discussions.

    Not production-ready: real deployment should track quota usage (each
    search call costs ~100 units against the 10,000/day free tier, each
    comment page ~1 unit), paginate beyond the first page, and track
    connector health per docs/SOURCE_CONNECTORS.md. A video with comments
    disabled or a quota error is skipped for that video only, rather than
    failing the whole run - see FR-005 (no fabricated data over a hard stop).
    """

    source_type = "social"
    platform = "youtube"

    def __init__(
        self,
        query: str,
        api_key: str,
        max_videos: int = 5,
        max_comments_per_video: int = 20,
    ):
        self.query = query
        self.api_key = api_key
        self.max_videos = max_videos
        self.max_comments_per_video = max_comments_per_video

    def collect(self, query: str | None = None, since: datetime | None = None) -> Iterable[RawRecord]:
        collected_at = datetime.now(timezone.utc)
        for video_id, video_title in self._search_videos(query or self.query):
            yield from self._collect_comments(video_id, video_title, collected_at)

    def _get_json(self, url: str) -> dict | None:
        request = urllib.request.Request(url, headers={"User-Agent": "gcia-reference-connector/0.1"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404):
                # comments disabled, quota exceeded, or video unavailable -
                # skip rather than fabricate or crash the whole run.
                return None
            raise

    def _search_videos(self, search_query: str) -> Iterable[tuple[str, str | None]]:
        params = urllib.parse.urlencode(
            {
                "part": "snippet",
                "type": "video",
                "order": "relevance",
                "maxResults": self.max_videos,
                "q": search_query,
                "key": self.api_key,
            }
        )
        payload = self._get_json(f"{_API_BASE}/search?{params}")
        if not payload:
            return
        for item in payload.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue  # no connector-owned identifier: skip rather than invent one (FR-005)
            yield video_id, item.get("snippet", {}).get("title")

    def _collect_comments(
        self, video_id: str, video_title: str | None, collected_at: datetime
    ) -> Iterable[RawRecord]:
        params = urllib.parse.urlencode(
            {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": self.max_comments_per_video,
                "order": "relevance",
                "textFormat": "plainText",
                "key": self.api_key,
            }
        )
        payload = self._get_json(f"{_API_BASE}/commentThreads?{params}")
        if not payload:
            return
        for item in payload.get("items", []):
            top_comment = item.get("snippet", {}).get("topLevelComment", {})
            comment_id = top_comment.get("id")
            if not comment_id:
                continue  # no connector-owned identifier: skip rather than invent one (FR-005)
            snippet = top_comment.get("snippet", {})
            yield RawRecord(
                platform=self.platform,
                source_native_id=comment_id,
                original_url=f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}",
                author_public_name=snippet.get("authorDisplayName"),
                published_at=_parse_youtube_timestamp(snippet.get("publishedAt")),
                collected_at=collected_at,
                title=video_title,
                content=snippet.get("textDisplay") or snippet.get("textOriginal") or "",
                engagement={
                    "score": int(snippet.get("likeCount") or 0),
                    "num_comments": int(item.get("snippet", {}).get("totalReplyCount") or 0),
                },
                raw_payload={
                    "video_id": video_id,
                    "authorDisplayName": snippet.get("authorDisplayName") or "",
                },
            )
