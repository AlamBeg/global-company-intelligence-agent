"""Point the test suite at its own throwaway SQLite database.

This must run before `gcia.common.config` is first imported anywhere, so it
sets the environment variable at module import time (pytest imports
conftest.py before collecting test modules) rather than inside a fixture -
by the time a fixture could run, Settings() would already have been
constructed from the dev .env's DATABASE_URL (gcia.db), and the test suite
would silently share schema/state with manual `python -m gcia...` runs.
"""
from __future__ import annotations

import os
import pathlib
import tempfile

_test_db_path = pathlib.Path(tempfile.mkdtemp(prefix="gcia_test_db_")) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"
