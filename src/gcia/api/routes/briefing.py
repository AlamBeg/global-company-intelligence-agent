from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse

from gcia.common.auth import require_role
from gcia.storage import repository
from gcia.storage.db import SessionLocal, init_db

router = APIRouter(prefix="/v1/briefings", tags=["briefing"])


def _render_markdown(summary: dict) -> str:
    s = summary["sentiment"]
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# {summary['canonical_name']} — Company Intelligence Briefing",
        f"_Generated {generated_at} · company_id: {summary['company_id']}_",
        "",
        "## Summary",
        f"- Discussions analyzed: {summary['discussion_count']}",
        (
            f"- Overall sentiment: {s['overall_score'] if s['overall_score'] is not None else 'n/a'} "
            f"(sample size {s['sample_size']}; positive {s['positive']}, neutral {s['neutral']}, "
            f"negative {s['negative']})"
        ),
        (
            f"- Duplicate/syndicated content grouped: {summary['narrative_dedup']['duplicate_clusters']} "
            f"cluster(s), {summary['narrative_dedup']['duplicate_discussions_grouped']} discussion(s) "
            "(not double-counted as independent opinions)"
        ),
        "",
        "## Top Topics",
    ]
    if summary["topics"]:
        lines += [f"- {t['label']} (volume {t['volume']}, confidence {t['confidence']:.2f})" for t in summary["topics"]]
    else:
        lines.append("_No topics computed yet - run `python -m gcia.workflows.run_company_window`._")

    lines += ["", "## Risk Summary"]
    if summary["risks"]:
        lines += [
            f"- **{r['category']}** (severity {r['severity']:.2f}, confidence {r['confidence']:.2f}): {r['summary']}"
            for r in summary["risks"]
        ]
    else:
        lines.append("_No risks computed yet - run `python -m gcia.workflows.run_company_window`._")

    lines += ["", "## Evidence (every material claim above traces to a record here)"]
    if summary["evidence"]:
        for e in summary["evidence"]:
            url = e["original_url"] or "_no verifiable source URL_"
            lines.append(
                f"- {e['claim_supported']} (confidence {e['confidence']:.2f}): "
                f"\"{e['excerpt']}\" — {url}"
            )
    else:
        lines.append("_No evidence recorded yet._")

    lines += [
        "",
        "## Coverage limitations",
        (
            "- This briefing reflects only sources actually ingested for this company; a missing "
            "platform or region is not evidence that no discussion exists there."
        ),
        (
            "- Sentiment, topic, and risk figures depend on a real model key being configured at "
            "analysis time - placeholder-mode runs are not real analysis."
        ),
    ]
    return "\n".join(lines)


@router.post("/{company_id}/export")
def export_briefing(
    company_id: str, format: str = "markdown", role: str = Depends(require_role("analyst"))
) -> Response:
    """FR-032 executive briefing export. Preserves evidence links, confidence,
    and coverage limitations rather than presenting bare numbers. Requires
    'analyst' role or above (NFR-011) - exports are more sensitive than the
    dashboard view.

    Only markdown and json are implemented; PDF/slide export (mentioned in
    the PRD) is not built yet - see docs/MVP_ROADMAP.md.
    """
    if format not in ("markdown", "json"):
        raise HTTPException(status_code=400, detail="format must be 'markdown' or 'json'")

    init_db()
    session = SessionLocal()
    try:
        summary = repository.get_company_summary(session, company_id)
    finally:
        session.close()
    if summary is None:
        raise HTTPException(status_code=404, detail="company not found - run ingestion first")

    if format == "json":
        return JSONResponse(summary)

    return Response(content=_render_markdown(summary), media_type="text/markdown")
