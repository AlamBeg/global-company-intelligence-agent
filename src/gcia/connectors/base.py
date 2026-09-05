from __future__ import annotations

from datetime import datetime
from typing import Iterable, Protocol

from gcia.schemas.discussion import RawRecord


class Connector(Protocol):
    """Common interface every source connector implements
    (docs/SOURCE_CONNECTORS.md "Connector principles"). The connector is the
    sole owner of original_url and source_native_id - nothing downstream may
    invent either (FR-005)."""

    source_type: str
    platform: str

    def collect(self, query: str | None, since: datetime | None = None) -> Iterable[RawRecord]:
        ...
