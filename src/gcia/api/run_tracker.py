"""In-memory tracker for live pipeline runs triggered from the dashboard.

Process-local by design, same single-laptop-demo scope as the rest of the
API (docs/IMPLEMENTATION_STATUS.md) - a restart loses in-flight run history,
which is fine since it only exists to drive a live status view, not an
audit trail (that's what the discussions/evidence tables are for).
"""
from __future__ import annotations

import threading
import time
import uuid

_MAX_EVENTS = 200


class RunTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: dict[str, dict] = {}

    def start(self, company_id: str, company_name: str) -> str:
        run_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._runs[run_id] = {
                "run_id": run_id,
                "company_id": company_id,
                "company_name": company_name,
                "status": "running",  # running | done | error
                "phase": "starting",  # starting | lane1 | lane2 | done
                "started_at": time.time(),
                "finished_at": None,
                "error": None,
                "progress": {"item": 0, "total": 0},
                "agents": {},  # agent_name -> {status, detail, updated_at}
                "events": [],  # newest last, capped
            }
        return run_id

    def set_phase(self, run_id: str, phase: str) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if run:
                run["phase"] = phase

    def set_progress(self, run_id: str, item: int, total: int) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if run:
                run["progress"] = {"item": item, "total": total}

    def update(self, run_id: str, agent: str, status: str, detail: str | None = None) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return
            now = time.time()
            run["agents"][agent] = {"status": status, "detail": detail, "updated_at": now}
            run["events"].append({"ts": now, "agent": agent, "status": status, "detail": detail})
            if len(run["events"]) > _MAX_EVENTS:
                run["events"] = run["events"][-_MAX_EVENTS:]

    def finish(self, run_id: str, error: str | None = None) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return
            run["status"] = "error" if error else "done"
            run["phase"] = "done"
            run["error"] = error
            run["finished_at"] = time.time()

    def get(self, run_id: str) -> dict | None:
        with self._lock:
            run = self._runs.get(run_id)
            return dict(run) if run else None


tracker = RunTracker()
