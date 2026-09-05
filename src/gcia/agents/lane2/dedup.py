from __future__ import annotations

from gcia.common.agent import Agent, ModelTier
from gcia.common.context import RunContext
from gcia.schemas.discussion import Discussion
from gcia.schemas.narrative import DuplicateCluster

_SHINGLE_SIZE = 5
_SIMILARITY_THRESHOLD = 0.8


def _shingles(text: str) -> set[str]:
    words = text.lower().split()
    return {
        " ".join(words[i : i + _SHINGLE_SIZE])
        for i in range(max(len(words) - _SHINGLE_SIZE + 1, 1))
    }


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class DeduplicationAgent(Agent[list[Discussion], list[DuplicateCluster]]):
    """Groups near-duplicate discussions (reposts, syndication, copies)
    within a batch. Deterministic, no LLM call - this runs over every
    discussion in a window, so it must stay cheap (FR-016).

    Shingle+Jaccard is a placeholder; production should use MinHash/SimHash
    or embedding-distance for scale, per DATA_ARCHITECTURE.md.
    """

    name = "deduplication"
    version = "1.0"
    tier = ModelTier.NONE

    def run(self, input: list[Discussion], context: RunContext) -> list[DuplicateCluster]:
        shingles = {d.discussion_id: _shingles(d.content) for d in input}
        assigned: set[str] = set()
        clusters: list[DuplicateCluster] = []

        for i, d in enumerate(input):
            if d.discussion_id in assigned:
                continue
            members = [d.discussion_id]
            for other in input[i + 1 :]:
                if other.discussion_id in assigned:
                    continue
                score = _jaccard(shingles[d.discussion_id], shingles[other.discussion_id])
                if score >= _SIMILARITY_THRESHOLD:
                    members.append(other.discussion_id)
                    assigned.add(other.discussion_id)
            if len(members) > 1:
                assigned.update(members)
                clusters.append(
                    DuplicateCluster(
                        cluster_id=f"dup:{members[0]}",
                        canonical_discussion_id=members[0],
                        member_discussion_ids=members,
                        derivative_type="copy",
                        similarity_score=_SIMILARITY_THRESHOLD,
                        confidence=0.7,
                    )
                )
        return clusters
