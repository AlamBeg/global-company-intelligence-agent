# Evidence and Provenance

## Core rule

Every material intelligence claim must be traceable to one or more source records. The source/collection layer owns URLs; AI components may reference them but must not fabricate them.

## Evidence chain

```text
Original source
  -> Raw source record
  -> Normalized discussion
  -> Analytical assessments
  -> Evidence object
  -> Claim / Topic / Risk / Trend
  -> User-facing insight
```

## Evidence object

Required fields should include:

- evidence_id
- source_record_id
- original_url
- source/platform
- observed_at/published_at
- claim supported
- evidence excerpt or permitted representation
- language
- geography and confidence
- relevance
- analytical labels
- evidence confidence
- model/version metadata
- created_at

## Verification states

- URL verified
- URL inaccessible
- content changed
- source deleted
- paywall/restricted
- source unavailable
- evidence insufficient

The UI must not hide these states.

## Claim grounding

Generated claims should cite the smallest useful set of independent evidence records. The system should distinguish direct observation, source-reported claims, inferred patterns, and model interpretation.

## Narrative independence

When multiple sources repeat the same underlying event, the system should present a narrative cluster and identify source relationships. This prevents apparent consensus from being created by syndication.

## Audit trail

Store the analytical component, model/version, configuration, timestamp, input IDs, and output for important intelligence decisions. Where raw data retention is restricted, preserve only the metadata legally permitted.

## URL safety

Never generate a source URL from a guessed slug, title, or search result unless the connector has deterministically produced and validated it. If no stable original URL exists, say so.
