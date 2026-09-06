from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from io import BytesIO

from gcia.connectors.reddit_public import RedditPublicConnector
from gcia.connectors.rss_news import RssNewsConnector
from gcia.connectors.youtube_public import YouTubeConnector

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_rss_connector_never_yields_a_record_without_a_native_id():
    feed_uri = (_FIXTURES / "sample_feed.xml").resolve().as_uri()
    records = list(RssNewsConnector(feed_uri).collect())

    assert len(records) == 3
    assert all(r.source_native_id for r in records)
    assert all(r.original_url and r.original_url.startswith("https://") for r in records)


def test_rss_connector_parses_real_pub_dates():
    feed_uri = (_FIXTURES / "sample_feed.xml").resolve().as_uri()
    records = {r.source_native_id: r for r in RssNewsConnector(feed_uri).collect()}

    assert records["acme-earnings-q3"].published_at == datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    assert records["acme-support-complaints"].published_at == datetime(
        2026, 9, 2, 14, 30, tzinfo=timezone.utc
    )


def test_rss_connector_leaves_published_at_none_when_pub_date_missing():
    feed_uri = (_FIXTURES / "sample_feed.xml").resolve().as_uri()
    records = {r.source_native_id: r for r in RssNewsConnector(feed_uri).collect()}

    assert records["weather-weekend"].published_at is None


def test_reddit_connector_skips_items_with_no_native_id():
    listing_uri = (_FIXTURES / "reddit_listing.json").resolve().as_uri()
    records = list(RedditPublicConnector(listing_uri).collect())

    # 3 items in the fixture; all three actually have an id (Reddit always
    # assigns one, even to removed posts) but the "no-permalink-item" case
    # exercises the None-original_url path instead - see the FR-005 required-
    # but-nullable field on RawRecord.
    assert len(records) == 3
    ids = {r.source_native_id for r in records}
    assert ids == {"abc123", "def456", "no-permalink-item"}

    no_permalink = next(r for r in records if r.source_native_id == "no-permalink-item")
    assert no_permalink.original_url is None


def test_reddit_connector_maps_engagement_metrics():
    listing_uri = (_FIXTURES / "reddit_listing.json").resolve().as_uri()
    records = {r.source_native_id: r for r in RedditPublicConnector(listing_uri).collect()}

    assert records["abc123"].engagement == {"score": 42, "num_comments": 7}
    assert records["abc123"].original_url == (
        "https://www.reddit.com/r/technology/comments/abc123/acme_corp_just_shipped_a_great_update/"
    )


_YOUTUBE_SEARCH_RESPONSE = {
    "items": [
        {"id": {"videoId": "vid1"}, "snippet": {"title": "Tesla Cybertruck review"}},
        {"id": {"kind": "youtube#channel"}, "snippet": {"title": "no videoId - should be skipped"}},
    ]
}

_YOUTUBE_COMMENTS_RESPONSE = {
    "items": [
        {
            "snippet": {
                "topLevelComment": {
                    "id": "comment1",
                    "snippet": {
                        "authorDisplayName": "@some_fan",
                        "textDisplay": "This car looks amazing!",
                        "likeCount": 12,
                        "publishedAt": "2026-09-04T12:34:56Z",
                    },
                },
                "totalReplyCount": 3,
            }
        },
        {
            "snippet": {
                "topLevelComment": {"snippet": {"textDisplay": "no id - should be skipped"}},
                "totalReplyCount": 0,
            }
        },
    ]
}


def _fake_urlopen(request, timeout=10):
    url = request.full_url if hasattr(request, "full_url") else request
    payload = _YOUTUBE_COMMENTS_RESPONSE if "commentThreads" in url else _YOUTUBE_SEARCH_RESPONSE
    return BytesIO(json.dumps(payload).encode())


def test_youtube_connector_skips_search_results_without_a_video_id(monkeypatch):
    monkeypatch.setattr("gcia.connectors.youtube_public.urllib.request.urlopen", _fake_urlopen)
    records = list(YouTubeConnector("Tesla", api_key="fake-key").collect())

    assert len(records) == 1
    assert records[0].source_native_id == "comment1"


def test_youtube_connector_maps_engagement_and_url(monkeypatch):
    monkeypatch.setattr("gcia.connectors.youtube_public.urllib.request.urlopen", _fake_urlopen)
    records = list(YouTubeConnector("Tesla", api_key="fake-key").collect())

    record = records[0]
    assert record.platform == "youtube"
    assert record.title == "Tesla Cybertruck review"
    assert record.content == "This car looks amazing!"
    assert record.author_public_name == "@some_fan"
    assert record.engagement == {"score": 12, "num_comments": 3}
    assert record.original_url == "https://www.youtube.com/watch?v=vid1&lc=comment1"
    assert record.published_at == datetime(2026, 9, 4, 12, 34, 56, tzinfo=timezone.utc)
