from __future__ import annotations

from gcia.api.run_tracker import RunTracker


def test_lifecycle_tracks_agent_status_and_events():
    tracker = RunTracker()
    run_id = tracker.start("acme", "Acme Corp")

    tracker.set_phase(run_id, "lane1")
    tracker.set_progress(run_id, 1, 3)
    tracker.update(run_id, "Normalization", "running")
    tracker.update(run_id, "Normalization", "done")
    tracker.finish(run_id)

    run = tracker.get(run_id)
    assert run["status"] == "done"
    assert run["phase"] == "done"
    assert run["progress"] == {"item": 1, "total": 3}
    assert run["agents"]["Normalization"]["status"] == "done"
    assert len(run["events"]) == 2
    assert run["error"] is None


def test_finish_with_error_sets_error_status():
    tracker = RunTracker()
    run_id = tracker.start("acme", "Acme Corp")
    tracker.finish(run_id, error="boom")

    run = tracker.get(run_id)
    assert run["status"] == "error"
    assert run["error"] == "boom"


def test_unknown_run_id_returns_none():
    tracker = RunTracker()
    assert tracker.get("does-not-exist") is None


def test_updates_on_unknown_run_id_do_not_raise():
    tracker = RunTracker()
    tracker.update("nope", "Normalization", "running")
    tracker.set_phase("nope", "lane1")
    tracker.set_progress("nope", 1, 2)
    tracker.finish("nope")
    assert tracker.get("nope") is None
