from __future__ import annotations

from gcia.schemas.discussion import Discussion

_TOPIC_SIMILARITY_THRESHOLD = 0.3


def _words(text: str) -> set[str]:
    return set(text.lower().split())


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def naive_topic_clusters(discussions: list[Discussion]) -> list[list[Discussion]]:
    """Groups discussions by loose lexical (word-overlap) similarity so
    TopicAgent/NarrativeAgent run once per cluster instead of once per
    discussion (the cost rationale in MULTI_AGENT_ARCHITECTURE.md "Lane 2").

    Placeholder: production clustering should use embedding distance in the
    vector store (DATA_ARCHITECTURE.md "Vector store") to catch paraphrased
    or multilingual matches that raw word overlap misses. The threshold is
    intentionally looser than DeduplicationAgent's shingle-based one - this
    groups *related* discussion, not just near-duplicates.
    """
    word_sets = {d.discussion_id: _words(d.content) for d in discussions}
    assigned: set[str] = set()
    clusters: list[list[Discussion]] = []

    for i, d in enumerate(discussions):
        if d.discussion_id in assigned:
            continue
        members = [d]
        assigned.add(d.discussion_id)
        for other in discussions[i + 1 :]:
            if other.discussion_id in assigned:
                continue
            score = _jaccard(word_sets[d.discussion_id], word_sets[other.discussion_id])
            if score >= _TOPIC_SIMILARITY_THRESHOLD:
                members.append(other)
                assigned.add(other.discussion_id)
        clusters.append(members)
    return clusters
