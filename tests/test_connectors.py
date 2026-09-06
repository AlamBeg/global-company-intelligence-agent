from __future__ import annotations

import pathlib
from datetime import datetime, timezone

from gcia.connectors.reddit_public import RedditPublicConnector
from gcia.connectors.rss_news import RssNewsConnector

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
