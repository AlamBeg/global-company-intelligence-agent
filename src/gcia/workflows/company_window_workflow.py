from __future__ import annotations

from gcia.agents.lane2.dedup import DeduplicationAgent
from gcia.common.context import RunContext
from gcia.schemas.discussion import Discussion
from gcia.workflows.runner import DagRunner


def build_company_window_workflow(discussions: list[Discussion], context: RunContext) -> DagRunner:
    """Lane 2 for one (company_id, time_window). Each node corresponds to one
    batch agent from MULTI_AGENT_ARCHITECTURE.md "Lane 2"; wire in Topic,
    Narrative, Credibility, Trend, and Risk the same way once their inputs
    (embeddings, source history) are available.
    """
    runner = DagRunner()
    runner.add("dedup", lambda _inputs: DeduplicationAgent().run(discussions, context))
    return runner
