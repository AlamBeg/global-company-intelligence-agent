from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Node:
    name: str
    fn: Callable[[dict[str, Any]], Any]
    depends_on: list[str] = field(default_factory=list)


class DagRunner:
    """In-process, topologically-ordered DAG executor.

    Stands in for a durable workflow engine (Temporal/Airflow-class) - see
    MULTI_AGENT_ARCHITECTURE.md "Lane 2 - Batch, per company/window". It
    intentionally has no retry/checkpoint persistence; swap the body of
    run() for a Temporal workflow once Lane 2 needs to survive process
    restarts and run at production volume.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}

    def add(
        self, name: str, fn: Callable[[dict[str, Any]], Any], depends_on: list[str] | None = None
    ) -> None:
        self.nodes[name] = Node(name=name, fn=fn, depends_on=depends_on or [])

    def run(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        remaining = dict(self.nodes)
        while remaining:
            ready = [n for n in remaining.values() if all(d in results for d in n.depends_on)]
            if not ready:
                raise RuntimeError(f"cycle or missing dependency among: {list(remaining)}")
            for node in ready:
                inputs = {d: results[d] for d in node.depends_on}
                results[node.name] = node.fn(inputs)
                del remaining[node.name]
        return results
