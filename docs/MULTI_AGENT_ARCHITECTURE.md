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
