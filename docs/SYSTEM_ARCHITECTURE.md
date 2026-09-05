# System Architecture

## 1. Architecture goals

The architecture must support global public/authorized-source intelligence at scale while preserving provenance, source URLs, multilingual semantics, independent scoring dimensions, and explainability.

## 2. Logical layers

1. API/UI layer
2. Orchestration layer
3. Entity and discovery layer
4. Connector/collection layer
5. Event bus and workflow layer
6. Raw and normalized storage
7. AI understanding layer
8. Narrative/deduplication layer
9. Intelligence/scoring layer
10. Retrieval and knowledge layer
11. Synthesis layer
12. Monitoring/alerting layer

## 3. Flow

```text
Client
  -> API Gateway
  -> Orchestrator
  -> Entity Resolution + Discovery
  -> Connector Planner
  -> Source Connectors
  -> Event Bus
  -> Raw Object Store
  -> Normalization
  -> Language / Relevance / Entity
  -> Sentiment / Topic / Emotion / Intent / Claims / Geography
  -> Deduplication / Narrative Graph
  -> Impact / Credibility
  -> Trend / Risk
  -> Verification
  -> Search + Vector + Graph + Analytics
  -> Analyst/Synthesis
  -> API / Dashboard / Alerts
```

## 4. Recommended infrastructure

Technology choices are implementation decisions, but the system should have equivalents for:

- Durable event streaming/queueing
- Object storage for raw source payloads
- Relational/analytical storage
- Full-text search
- Vector retrieval
- Graph storage
- Cache
- Workflow orchestration
- Model gateway
- Secrets management
- Observability

A possible stack is Kafka-compatible streaming, object storage, PostgreSQL/ClickHouse-class analytics, OpenSearch-class retrieval, a vector database, and Neo4j-class graph storage. Components may be substituted based on deployment constraints.

## 5. Reliability

Each connector is independently retryable and observable. Processing must be idempotent. Poison messages move to a dead-letter queue. Backpressure must protect downstream models and databases.

## 6. Provenance

Raw source payloads and collection metadata are immutable where practical. Normalized records reference raw records. Analytical results reference normalized records. User-facing claims reference evidence IDs and original URLs.

## 7. Model gateway

All LLM/model calls should go through a versioned model gateway that records model, version, prompt/configuration version, latency, token/cost estimates, and structured output validation results.

## 8. API boundaries

The API should expose company profiles, discussions, evidence, topics, sentiment, trends, risks, narratives, source coverage, and monitoring configurations without exposing internal secrets or unrestricted raw connector credentials.

## 9. Multi-tenancy

Tenant isolation should exist at authentication, authorization, data, cache, search, vector, and alerting boundaries if the platform becomes multi-tenant.

## 10. Deployment

Containerized services should support local development, staging, and production deployments. Stateless workers should scale horizontally; stateful systems require explicit backup and recovery procedures.
