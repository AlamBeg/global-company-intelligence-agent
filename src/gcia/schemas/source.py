from __future__ import annotations

from pydantic import BaseModel


class Source(BaseModel):
    source_id: str
    platform: str
    source_type: str  # social, news, blog, forum, review, other
    access_method: str  # official_api, licensed_feed, public_web, authorized_crawl
    license_notes: str | None = None
