"""Isolate the test suite from the developer machine's actual environment.

Both of these must run before `gcia.common.config` is first imported
anywhere, so they set environment variables at module import time (pytest
imports conftest.py before collecting test modules) rather than inside a
fixture - by the time a fixture could run, Settings() would already have
been constructed from the dev .env.

- DATABASE_URL: without this, the test suite would silently share schema/
  state with manual `python -m gcia...` runs against gcia.db.
- GCIA_MODEL_PROVIDER: without this, tests that exercise real entrypoints
  (run_ingestion, run_company_window, the API routes) call
  resolve_provider(), which honors whatever provider .env has configured.
  If Ollama happens to be installed and running locally (as it is on this
  machine as of 2026-09-06), tests would silently start making real,
  slow, non-deterministic local-model calls instead of using the fast,
  deterministic MockProvider path every other test relies on. Pinning to
  "anthropic" with no key set forces the documented placeholder fallback
  regardless of what's actually installed/configured on the machine
  running the suite.
"""
from __future__ import annotations

import os
import pathlib
import tempfile

_test_db_path = pathlib.Path(tempfile.mkdtemp(prefix="gcia_test_db_")) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"

os.environ["GCIA_MODEL_PROVIDER"] = "anthropic"
os.environ["ANTHROPIC_API_KEY"] = ""
