"""Normalized operational store (docs/DATA_ARCHITECTURE.md "Normalized
operational store"). SQLite by default so the product runs with zero infra;
point DATABASE_URL at Postgres (see docker-compose.yml) once this needs to
run outside a single laptop.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gcia.common.config import settings

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, future=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    from gcia.storage.models import Base

    Base.metadata.create_all(bind=engine)
