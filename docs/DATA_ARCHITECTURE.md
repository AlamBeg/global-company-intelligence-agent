# Data Architecture

## 1. Storage domains

### Raw store
Immutable or append-only source payloads, connector metadata, collection timestamps, and source identifiers.

### Normalized operational store
Canonical company, source, author, discussion, claim, topic, narrative, evidence, risk, and alert records.

### Search index
Keyword and filter retrieval over normalized discussion/evidence metadata and searchable text.

### Vector store
Semantic and multilingual embeddings for discussion retrieval, clustering, duplicate detection, and cross-language matching.

### Knowledge graph
Relationships among Company, Brand, Product, Person, Discussion, Source, Topic, Narrative/Event, Claim, Risk, Country, Language, and Competitor.

### Analytics store
Time series, aggregates, score histories, topic velocity, source distribution, and dashboard metrics.

## 2. Canonical discussion record

A Discussion should include:

- discussion_id
- source_id
- original_url
- platform
- source_type
- author_id/public_name where permitted
- published_at
- collected_at
- language
- country/region
- title
- content/excerpt
- engagement metrics
- parent/repost identifiers
- raw_record_id
- content_hash
- semantic_fingerprint
- entity_candidates
- relevance assessment
- processing/model versions

## 3. Evidence model

Evidence is the bridge between source data and intelligence. It should point to the original discussion and contain the exact source URL, source timestamp, analytical labels, and the claim/insight that uses it.

## 4. Deduplication model

Do not delete duplicate source records merely because they are similar. Preserve source records and attach:

- duplicate_cluster_id
- canonical/origin record
- derivative type: repost, syndication, quote, translation, copy, update
- similarity score
- relationship confidence

Analytics should be able to count unique narratives and unique source records separately.

## 5. Versioning

Scores, classifiers, embeddings, prompts, taxonomy versions, and schemas must be versioned. Historical results must retain the version used to create them.

## 6. Retention

Retention is configurable by source and tenant and must respect licensing, legal requirements, platform terms, and deletion requests. Where raw content cannot be retained, store permitted metadata and evidence pointers.

## 7. Data quality checks

Validate required IDs, timestamps, URL syntax, language consistency, source identity, duplicate keys, schema version, and analytical confidence. Invalid records go to quarantine/dead-letter workflows.
