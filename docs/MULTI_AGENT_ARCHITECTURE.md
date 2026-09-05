# Multi-Agent Architecture

## Agent responsibilities

### Orchestrator Agent
Owns workflow planning, budgets, retries, prioritization, and final task state. It does not independently invent source URLs or bypass connector policies.

### Company Entity Agent
Resolves the requested company against canonical identifiers, aliases, products, subsidiaries, domains, tickers, executives, local names, and ambiguous-name candidates.

### Discovery Agent
Generates search queries and source candidates. It expands vocabulary from discovered terminology while preventing uncontrolled query explosion.

### Source Agents
Source-specific workers call approved APIs, feeds, search services, or authorized crawlers. They preserve source-native identifiers and original URLs.

### Normalization Agent
Maps heterogeneous source payloads to canonical Discussion, Author, Source, Media, and Engagement schemas.

### Language Agent
Detects language, script, transliteration, mixed-language content, and semantic equivalents across languages.

### Relevance Agent
Scores company/entity relevance and identifies why an item is relevant. Low-confidence items can be quarantined for later review.

### Sentiment Agent
Produces overall and aspect-level sentiment, intensity, and confidence. It must not use reach or credibility as sentiment inputs unless explicitly part of a separate model.

### Topic Agent
Creates topic embeddings/clusters, labels clusters, and identifies emerging topics.

### Emotion Agent
Extracts emotional states and confidence.

### Intent Agent
Extracts purchase, churn, advocacy, complaint, recommendation, support, comparison, investment, or other behavior signals where appropriate.

### Claim Agent
Extracts claims and separates reported statements from model interpretations.

### Narrative Agent
Builds event/narrative clusters across platforms and time, identifying origin/derivative relationships where evidence supports them.

### Deduplication Agent
Finds exact/near duplicates, syndication, reposts, translations, and copies. It produces cluster IDs rather than deleting evidence blindly.

### Impact Agent
Estimates discussion importance using configurable reach, engagement, influence, credibility, velocity, topic importance, and propagation signals.

### Credibility Agent
Evaluates source/author reliability signals. It does not certify truth.

### Geography Agent
Determines location from explicit or reliable inferred evidence and assigns confidence.

### Trend Agent
Compares time windows and identifies statistically or operationally meaningful changes.

### Risk Agent
Transforms observed signals into ranked risk objects with severity, momentum, affected dimensions, evidence, and confidence.

### Verification Agent
Checks source accessibility, URL integrity, evidence relevance, provenance consistency, and support for material claims.

### Synthesis Agent
Produces concise company intelligence from structured outputs and evidence. It must preserve uncertainty and citations/links to source evidence.

## Agent contract principles

- Structured JSON-like schemas between agents
- Schema and model versions on every analytical object
- Deterministic IDs for source records
- Idempotent processing
- Explicit confidence
- Explicit provenance
- Bounded context passed to LLMs
- No direct access to secrets unless required by connector runtime
- Human review for high-impact ambiguous cases

## Execution model

Twenty-one agent responsibilities do not imply twenty-one chained LLM calls per item, or one long-running agent loop per query. Agents run in three lanes, split by trigger and cadence rather than by org chart, so a failure or slowdown in one lane cannot stall the others (NFR-001) and reprocessing stays cheap and idempotent (NFR-006).

### Lane 1 — Streaming, per item

Trigger: each normalized discussion record, as it arrives off the event bus.

Agents: Normalization, Language, Relevance, Sentiment, Emotion, Intent, Claim, per-item Geography.

Shape: stateless consumer workers, one pool per agent type, horizontally scaled, keyed by `discussion_id`. Each agent is a pure function of `(input, agent_version)`, cached by `(content_hash, agent_version)` — so a prompt or model upgrade only reprocesses new/changed content, not the full history. Low-confidence Relevance/Sentiment outputs route to the human-review queue instead of blocking the pipeline.

### Lane 2 — Batch, per company/window

Trigger: schedule or volume threshold, scoped to `(company_id, time_window)`.

Agents: Deduplication, Topic clustering/labeling, Narrative clustering, Impact, Credibility, Trend, Risk.

Shape: durable workflow-engine jobs (Temporal/Airflow-class), because these agents read a window of already-processed Lane 1 output rather than one record at a time. Each run is versioned (`score_model_version`, `taxonomy_version`) and idempotent per `(company_id, window, version)`, so a retried or re-triggered run does not double-count.

### Lane 3 — On-demand, per query

Trigger: user query, dashboard load, comparison request (FR-031), or briefing export (FR-032).

Agents: Discovery (only invoked when existing coverage is insufficient for the query), Verification, Synthesis/Analyst.

Shape: request/response service with a bounded latency budget (NFR-012). Synthesis is retrieval over already-computed Lane 1/2 outputs and the evidence store — it does not recompute upstream scores.

## Orchestrator responsibilities in practice

The Orchestrator is a control-plane, not a participant in analysis: it starts and tracks Lane 2 workflow runs with retry/backoff, enforces per-run budgets (max discovery queries, max tokens/cost), and exposes circuit-breaker state per connector/agent so one bad source or agent cannot stall Lane 1. It never calls an LLM and never touches source URLs directly.

## Agent interface contract

Every agent — LLM-backed or deterministic — implements the same shape: `run(input: TypedModel, context: RunContext) -> TypedOutput`. `RunContext` carries `trace_id`, `tenant_id`, budget, and pinned model/prompt versions. This uniformity is what lets the Orchestrator retry, log, and dead-letter 21 different agents identically instead of special-casing each one.

LLM-backed agents additionally:

- Return structured output only (JSON-schema/function-calling mode) — never freeform prose passed downstream.
- Receive bounded context: only the fields the agent needs (e.g., Sentiment never sees engagement/reach), which is also what keeps sentiment independent of impact per the scoring model.
- Report confidence that is calibrated separately from the model's self-reported certainty (e.g., a small classifier or lookup against that agent's evaluation-set performance for similar inputs).
- Route every call through the model gateway so model, version, latency, and cost are logged per call against the same `trace_id`.

## Determinism and idempotency

Discussion IDs are deterministic (`hash(platform, source_native_id)`), so re-ingestion never creates duplicate records. Agent outputs are content-addressed by `(input_hash, agent_version)`, so reprocessing after a model or prompt upgrade only recomputes what actually changed.

## Human-in-the-loop routing

A single review queue service — not one per agent — receives low-confidence output from Entity Resolution, Relevance, and Risk. Reviewer decisions write back into the evaluation datasets, closing the feedback loop rather than only fixing the one flagged case.
