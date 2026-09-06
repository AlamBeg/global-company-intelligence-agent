from __future__ import annotations

import pathlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from gcia.api.routes import ask, briefing, company, compare, discovery, entity, evidence, pipeline, trend

app = FastAPI(
    title="Global Company Intelligence Agent API",
    version="0.1.0",
    description="Lane 3 (on-demand) surface: company profiles, evidence, comparisons, and briefings.",
)

app.include_router(entity.router)
app.include_router(company.router)
app.include_router(evidence.router)
app.include_router(compare.router)
app.include_router(briefing.router)
app.include_router(ask.router)
app.include_router(trend.router)
app.include_router(discovery.router)
app.include_router(pipeline.router)

_static_dir = pathlib.Path(__file__).parent / "static"
app.mount("/dashboard", StaticFiles(directory=_static_dir, html=True), name="dashboard")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
