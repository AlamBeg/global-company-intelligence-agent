from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.common.ids import content_hash, discussion_id
from gcia.schemas.discussion import Discussion, RawRecord


class NormalizationAgent(Agent[RawRecord, Discussion]):
    """Deterministic mapping from a connector's RawRecord to the canonical
    Discussion schema. No LLM call - see FR-006 / DATA_ARCHITECTURE.md.
    """

    name = "normalization"
    version = "1.0"
    tier = ModelTier.NONE

    def run(self, input: RawRecord, context: RunContext) -> Discussion:
        did = discussion_id(input.platform, input.source_native_id)
        return Discussion(
            discussion_id=did,
            source_id=input.platform,
            original_url=input.original_url,
            url_status="verified" if input.original_url else "unavailable",
            platform=input.platform,
            source_type="unknown",
            author_id=input.author_public_name,
            published_at=input.published_at,
            collected_at=input.collected_at,
            title=input.title,
            content=input.content,
            engagement=input.engagement,
            parent_discussion_id=(
                discussion_id(input.platform, input.parent_native_id)
                if input.parent_native_id
                else None
            ),
            raw_record_id=f"{input.platform}:{input.source_native_id}",
            content_hash=content_hash(input.content),
        )
