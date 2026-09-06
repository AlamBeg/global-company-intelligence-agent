"""Live pipeline runs triggered from the dashboard: kicks off Lane 1
ingestion + Lane 2 window analysis for a company in a background thread and
lets the dashboard poll per-agent status while it runs (gcia.api.run_tracker).

This is a thin wrapper around the same entrypoints the CLI uses
(gcia.ingestion.run_ingestion, gcia.workflows.run_company_window) - it does
not duplicate pipeline logic, only adds status callbacks and async
triggering suited to a browser polling loop.
"""
from __future__ import annotations

import logging
import re
import threading
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from gcia.api.run_tracker import tracker
from gcia.common.auth import require_role
from gcia.ingestion import run_ingestion
from gcia.workflows import run_company_window

logger = logging.getLogger("gcia.api.pipeline")

router = APIRouter(prefix="/v1/runs", tags=["pipeline"])


class RunRequest(BaseModel):
    company_name: str
    company_id: str | None = None
    connector: str = "rss"
    feed_url: str | None = None
    limit: int | None = 8


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "company"


def _default_feed_url(connector: str, company_name: str) -> str:
    if connector == "rss":
        return f"https://news.google.com/rss/search?q={urllib.parse.quote(company_name)}"
    if connector == "youtube":
        return company_name  # YouTubeConnector treats this as the search query
    raise HTTPException(
        status_code=400,
        detail=f"--feed-url is required for connector {connector!r} (no default query URL)",
    )


def _execute(run_id: str, company_id: str, company_name: str, connector: str, feed_url: str, limit: int | None) -> None:
    def on_step(agent: str, status: str, detail: str | None) -> None:
        tracker.update(run_id, agent, status, detail)

    def on_progress(item: int, total: int | None) -> None:
        tracker.set_progress(run_id, item, total or 0)

    try:
        tracker.set_phase(run_id, "lane1")
        run_ingestion.run(
            company_id,
            company_name,
            feed_url,
            connector_name=connector,
            limit=limit,
            on_step=on_step,
            on_progress=on_progress,
        )
        tracker.set_phase(run_id, "lane2")
        run_company_window.run(company_id, on_step=on_step)
        tracker.finish(run_id)
    except Exception as exc:  # noqa: BLE001 - reported to the dashboard, not swallowed
        logger.exception("live run %s failed", run_id)
        tracker.finish(run_id, error=str(exc))


@router.post("")
def start_run(body: RunRequest, role: str = Depends(require_role("analyst"))) -> dict:
    """Starts a live ingestion + analysis run for a company and returns a
    run_id to poll via GET /v1/runs/{run_id}. Requires 'analyst' or higher
    (NFR-011) since it triggers real model calls, unlike the read-only
    GET /v1/companies/{id}.
    """
    company_id = body.company_id or _slugify(body.company_name)
    feed_url = body.feed_url or _default_feed_url(body.connector, body.company_name)
    run_id = tracker.start(company_id, body.company_name)

    thread = threading.Thread(
        target=_execute,
        args=(run_id, company_id, body.company_name, body.connector, feed_url, body.limit),
        daemon=True,
    )
    thread.start()
    return {"run_id": run_id, "company_id": company_id}


@router.get("/{run_id}")
def get_run(run_id: str, role: str = Depends(require_role("viewer"))) -> dict:
    run = tracker.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run
