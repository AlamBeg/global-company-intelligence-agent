# Product Requirements — Global Company Intelligence Agent

## 1. Product definition

### 1.1 Goal

Build an AI-driven company intelligence agent that accepts a company, brand, ticker, product, executive, or related identifier and discovers, analyzes, and explains relevant public discussion from around the world.

The system is intended to answer questions such as:

- What are people saying about this company globally?
- Is sentiment improving or deteriorating?
- What topics are driving the change?
- Which issues are emerging fastest?
- Which countries, languages, communities, or customer segments are driving the discussion?
- Which sources and authors have the greatest impact or credibility?
- What are the major reputation, product, customer, employee, regulatory, or competitive risks?
- What evidence supports each conclusion?

### 1.2 Product positioning

The product is a **Global Company Intelligence Agent**, not merely a sentiment-analysis system. It combines discovery, multilingual understanding, entity resolution, narrative analysis, source intelligence, scoring, trend detection, risk analysis, and evidence-backed synthesis.

### 1.3 Coverage boundary

The platform should maximize coverage of publicly accessible and contractually authorized data. "Global" means broad worldwide coverage subject to source availability, APIs, licensing, regional restrictions, robots/access controls, rate limits, and platform terms. It must not claim complete access to private accounts, private groups, inaccessible content, or every post on every platform.

---

## 2. Users and use cases

### Primary users

- Corporate strategy and executive teams
- Product and customer-experience teams
- Brand/reputation teams
- PR and communications teams
- Competitive-intelligence teams
- Investor-relations and market-intelligence teams
- Risk and compliance teams
- Research and consulting teams
- Developers integrating intelligence through APIs

### Core use cases

1. Company reputation monitoring
2. Product/customer feedback intelligence
3. Competitive intelligence
4. Crisis and emerging-risk detection
5. PR and communications analysis
6. Market and regional sentiment analysis
7. Executive and investor briefing generation
8. Historical trend analysis
9. Evidence-backed question answering
10. Continuous monitoring and alerting

---

## 3. Functional requirements

### FR-001 — Company/entity input

The system shall accept company names, legal names, brand names, ticker symbols, product names, domains, subsidiaries, executives, aliases, local-language names, nicknames, and common misspellings.

### FR-002 — Entity resolution

The system shall resolve input identifiers to a canonical company entity and maintain relationships to subsidiaries, brands, products, domains, executives, tickers, and known aliases.

The system shall prevent false attribution when a company name overlaps with unrelated people, places, products, or common words.

### FR-003 — Dynamic discovery

The discovery layer shall generate and refine search vocabulary using aliases, local-language names, transliterations, abbreviations, product terminology, hashtags, common misspellings, and terms discovered from relevant discussions.

### FR-004 — Global source discovery

The system shall support an extensible connector framework for authorized public sources, including:

- Social platforms: Reddit, X, YouTube, TikTok, Instagram, Facebook, LinkedIn, Threads and other accessible platforms
- News and media
- Blogs and independent publications
- Industry and trade publications
- Public forums and communities
- Product/review sites
- Developer communities
- Financial discussion sources
- Public comments and other web pages
- Regional and local-language sources

Connector availability shall be represented explicitly rather than implying universal platform coverage.

### FR-005 — Original source URL

Every collected discussion/evidence record shall preserve the original source URL when available. AI-generated URLs are prohibited. A URL may only be surfaced when supplied or deterministically produced by the source/collection layer.

### FR-006 — Source metadata

Each source record shall capture, where available:

- Platform/source type
- Original URL
- Author/account identifier or public author name
- Publication timestamp
- Collection timestamp
- Language
- Country/region
- Title/headline
- Text/content excerpt or normalized content
- Engagement metrics
- Media metadata
- Parent/repost/reply relationships
- Source credibility signals
- Access/licensing metadata

### FR-007 — Multilingual understanding

The platform shall detect language and analyze content across supported languages without requiring all content to be translated into English first.

It shall support semantic clustering of the same underlying issue across different languages and preserve original-language evidence.

### FR-008 — Relevance classification

Each item shall receive a relevance assessment indicating whether it is materially about the target company/entity and why.

### FR-009 — Sentiment analysis

The system shall calculate:

- Overall sentiment
- Positive/neutral/negative distribution
- Aspect-level sentiment
- Sentiment confidence
- Sentiment intensity

Sentiment must remain distinct from reach, impact, source credibility, and importance.

### FR-010 — Emotion analysis

Where meaningful, the system shall classify emotions such as trust, anger, frustration, fear, excitement, disappointment, satisfaction, admiration, confusion, or uncertainty.

### FR-011 — Intent analysis

The system shall identify signals such as purchase intent, recommendation intent, churn intent, complaint intent, support-seeking, advocacy, comparison, investment interest, hiring interest, or boycott intent when evidence supports them.

### FR-012 — Topic discovery

The system shall dynamically discover discussion topics rather than relying only on a fixed taxonomy.

Topics shall be clusterable across languages, platforms, and time windows.

### FR-013 — Emerging topics

The system shall identify rapidly growing topics and provide growth rate, baseline volume, affected regions/platforms, representative evidence, and confidence.

### FR-014 — Claim extraction

The system shall extract material factual or experiential claims from discussions and connect them to source evidence.

Claims shall be represented separately from the model's interpretation of those claims.

### FR-015 — Narrative and event clustering

The system shall group discussions that refer to the same underlying event, announcement, controversy, product issue, or narrative.

It shall distinguish independent opinions from syndicated articles, copied content, reposts, quote-posts, translations, and derivative coverage.

### FR-016 — Deduplication

Near-duplicate and duplicate content shall be detected across source types and languages where feasible.

The system shall avoid interpreting thousands of copies of one article as thousands of independent opinions.

### FR-017 — Impact scoring

The system shall calculate an impact/importance score independently from sentiment.

Potential components include:

- Estimated reach
- Engagement
- Author/account influence
- Source credibility
- Topic importance
- Discussion velocity
- Originality
- Cross-source propagation

The exact formula shall be configurable and versioned.

### FR-018 — Source credibility

The platform shall score source credibility using transparent signals such as source history, author identity consistency, evidence quality, originality, specialization, engagement authenticity indicators, and corroboration.

Credibility shall not be presented as an absolute determination of truth.

### FR-019 — Geographic intelligence

The platform shall provide geographic breakdowns where reliable location evidence exists, including country, region, language, and market.

Location inference shall carry a confidence value and must not be presented as certain when inferred.

### FR-020 — Trend analysis

The system shall compare configurable time windows and identify:

- Sentiment changes
- Volume changes
- Topic growth/decline
- Impact changes
- Geographic shifts
- Source/platform shifts
- Narrative propagation

The trend agent shall explain likely drivers and cite supporting evidence.

### FR-021 — Risk intelligence

The platform shall identify and rank emerging risks across categories including:

- Reputation/PR
- Product quality
- Customer experience
- Employee/workplace
- Regulatory/legal
- Security/privacy
- Competitive
- Financial/business
- Supply/operational

Each risk shall include evidence, severity, momentum, affected segments, confidence, and recommended monitoring context.

### FR-022 — Evidence-backed synthesis

The analyst agent shall answer natural-language questions using retrieved evidence. Material conclusions shall contain traceable evidence references.

### FR-023 — Evidence object

A standard evidence object shall contain, where applicable:

- Claim
- Claim type
- Source URL
- Platform
- Source record ID
- Timestamp
- Author/source
- Language
- Country
- Relevance score
- Sentiment/aspect labels
- Topic IDs
- Impact score
- Credibility score
- Confidence
- Collection metadata

### FR-024 — Knowledge graph

The system shall maintain relationships among Company, Brand, Product, Person, Discussion, Source, Topic, Event/Narrative, Country, Language, Claim, Risk, and Competitor entities.

### FR-025 — Search and retrieval

Users shall be able to search by company, topic, keyword, source, platform, language, country, date range, sentiment, impact, risk, author, and narrative.

### FR-026 — Dashboard

The dashboard shall expose at minimum:

- Overall intelligence summary
- Sentiment distribution
- Discussion volume and velocity
- Top topics
- Emerging topics
- Aspect sentiment
- Geographic distribution
- Source/platform distribution
- Impact distribution
- Reputation/risk summary
- Trend timeline
- Narrative clusters
- Representative evidence with original links

### FR-027 — API

The system shall provide an API for company intelligence queries, evidence retrieval, scores, trends, topics, risks, and monitoring configuration.

### FR-028 — Alerts

Users shall be able to define alerts for configurable thresholds such as rapid negative sentiment change, emerging high-impact narratives, discussion spikes, or risk escalation.

### FR-029 — Historical analysis

Where source/licensing permits, the platform shall support historical data analysis and comparisons across configurable time ranges.

### FR-030 — Continuous monitoring

The system shall support scheduled/streaming collection where source capabilities permit, with clear freshness timestamps.

---

## 4. Multi-agent requirements

The architecture shall use specialized agents/services with explicit responsibilities rather than one unrestricted model call.

### Required logical agents

1. Orchestrator Agent — coordinates workflows and budgets
2. Company Entity Agent — resolves canonical company identity and aliases
3. Discovery Agent — expands search vocabulary and finds candidate sources
4. Source/Connector Agents — interact with source-specific APIs/feeds/crawlers
5. Normalization Agent — converts source records into a canonical schema
6. Language Agent — detects language and supports multilingual semantics
7. Relevance Agent — validates company/entity relevance
8. Sentiment Agent — computes sentiment/aspect sentiment
9. Topic Agent — discovers and clusters topics
10. Emotion Agent — detects emotional signals
11. Intent Agent — detects behavioral/purchase/recommendation intent
12. Claim Agent — extracts claims and evidence statements
13. Narrative Agent — clusters events and related discussion
14. Deduplication Agent — identifies duplicates, reposts, syndication, and copies
15. Impact Agent — estimates importance/reach/propagation
16. Credibility Agent — evaluates source quality signals
17. Geography Agent — derives location with confidence
18. Trend Agent — analyzes changes over time
19. Risk Agent — identifies and ranks risks
20. Verification Agent — validates URLs, evidence relevance, and provenance
21. Synthesis/Analyst Agent — produces user-facing intelligence

Agents shall exchange typed, versioned objects and produce structured outputs rather than only prose.

---

## 5. Scoring requirements

All scores shall be versioned and explainable.

Minimum dimensions:

- Sentiment score
- Sentiment confidence
- Relevance score
- Impact score
- Source credibility score
- Topic momentum
- Risk severity
- Risk momentum
- Evidence confidence

Example company-level output may contain an overall sentiment score such as 68/100, positive/neutral/negative percentages, volume change, impact, confidence, and risk. Example values are illustrative only and must never be presented as measured data unless actually calculated.

The system shall prevent double-counting of correlated evidence and narrative copies.

---

## 6. Non-functional requirements

### NFR-001 Reliability

Pipeline failures in one source shall not prevent processing of other sources.

### NFR-002 Scalability

The system shall scale horizontally across ingestion, processing, search, vector retrieval, and analytics workloads.

### NFR-003 Freshness

Every result shall expose collection/processing timestamps and source freshness where available.

### NFR-004 Explainability

Scores and generated insights shall be traceable to component outputs and evidence.

### NFR-005 Observability

Track connector health, queue lag, ingestion rates, processing latency, model latency, token/cost usage, error rates, data quality, and scoring drift.

### NFR-006 Idempotency

Repeated ingestion of the same source item shall not create uncontrolled duplicate records.

### NFR-007 Security

Secrets, connector credentials, user data, and private configuration must be protected using least privilege and encryption.

### NFR-008 Privacy

The system shall minimize personal data collection and provide configurable retention/deletion controls consistent with applicable requirements.

### NFR-009 Compliance

Connectors shall enforce platform terms, API policies, licensing, regional restrictions, rate limits, robots/access rules where applicable, and data-retention constraints.

### NFR-010 Auditability

Important scoring and synthesis decisions shall be reproducible from stored inputs, model/version metadata, prompts/configuration, and evidence references where legally and technically appropriate.

---

## 7. Data model requirements

Canonical objects should include at least:

- Company
- EntityAlias
- Product
- Person
- Source
- Author
- Discussion
- Media
- Claim
- Topic
- Narrative/Event
- SentimentAssessment
- IntentAssessment
- EmotionAssessment
- Geography
- Risk
- Evidence
- Trend
- Alert

Every analytical object should include identifiers, timestamps, schema/model versions, confidence, and provenance links as appropriate.

---

## 8. Architecture requirements

Target logical architecture:

```text
User / API
    |
Orchestrator
    |
Company Entity + Discovery + Source Planning
    |
Collection Layer (APIs / feeds / authorized crawling)
    |
Source-specific connectors
    |
Queue / Event Bus
    |
Raw Storage
    |
Normalization + Language + Entity/Relevance
    |
Understanding Agents
    |-- Sentiment
    |-- Topic
    |-- Emotion
    |-- Intent
    |-- Claims
    |-- Geography
    |
Narrative + Deduplication
    |
Impact + Credibility
    |
Trend + Risk
    |
Verification
    |
Search / Vector / Knowledge Graph / Analytics
    |
Synthesis / Analyst
    |
Dashboard + API + Alerts
```

The implementation may use services, workers, pipelines, or agent runtimes instead of literal independent LLM agents, provided the responsibilities and contracts remain explicit.

---

## 9. Acceptance criteria

The MVP is acceptable when all of the following are true:

1. A user can submit a company and receive a resolved canonical entity.
2. The system can discover relevant public/authorized discussions from multiple source classes.
3. Every returned discussion includes an original source URL when one exists.
4. The system rejects or flags records whose source URL cannot be verified.
5. Duplicate/reposted/syndicated content is grouped or marked rather than blindly counted as independent opinions.
6. At least one multilingual workflow can cluster semantically equivalent discussions across languages.
7. Sentiment is separated from impact and source credibility.
8. Topics and emerging topics are generated from data rather than only a hard-coded list.
9. Company-level trends include evidence for their explanations.
10. Risks include evidence, severity, momentum, and confidence.
11. User-facing insights expose supporting source records.
12. Connector failures, processing failures, and model errors are observable.
13. API/source restrictions are respected and coverage limitations are visible to users.
14. Scoring versions and analytical model versions are stored.

---

## 10. Evaluation requirements

Build evaluation datasets covering:

- Correct/incorrect entity resolution
- Relevance classification
- Multilingual sentiment
- Aspect sentiment
- Topic clustering
- Duplicate detection
- Narrative clustering
- Geographic inference
- Source credibility signals
- Risk classification
- Evidence-to-claim grounding
- URL/source verification

Metrics should include precision, recall, F1, calibration, clustering quality, duplicate-detection accuracy, grounding accuracy, latency, cost per analyzed item, and source coverage.

Human review must be available for ambiguous or high-impact cases.

---

## 11. Failure and safety requirements

The platform shall explicitly handle:

- Ambiguous company names
- Sarcasm and irony
- Mixed-language posts
- Machine-translated content
- Spam and bot-like activity
- Coordinated campaigns
- Fake engagement
- Source outages
- Deleted content
- Broken URLs
- Paywalled or inaccessible content
- Syndicated content
- Conflicting reports
- Unverified allegations
- Insufficient evidence

The analyst must distinguish observed discussion from verified fact. Allegations must not automatically become company facts.

---

## 12. Product phases

### Phase 0 — Foundation

- Canonical schemas
- Entity resolution
- Connector framework
- Raw storage
- Search/index foundation
- Evidence/provenance model
- Initial API

### Phase 1 — MVP

- 3–5 high-value source classes
- English + selected regional languages
- Sentiment
- Topics
- Deduplication
- Evidence links
- Basic dashboard
- Historical trending

### Phase 2 — Intelligence

- Multilingual semantic clustering
- Narrative graph
- Impact/credibility scoring
- Risk intelligence
- Geography
- Alerts
- Analyst agent

### Phase 3 — Global scale

- Broad source connector ecosystem
- More languages/regions
- Streaming ingestion
- Advanced graph analytics
- Continuous evaluation
- Enterprise governance
- Large-scale historical backfill

---

## 13. Definition of done for production readiness

Production readiness requires:

- Documented architecture and data contracts
- Connector compliance review
- Automated tests and evaluation suites
- Observability dashboards
- Secure secret management
- Rate-limit handling
- Backpressure and retry policies
- Data retention/deletion controls
- Disaster recovery strategy
- Cost controls
- Model/version registry
- Evidence traceability
- Human escalation workflow
- Documented known coverage limitations

## 14. Guiding principle

**The AI should never merely say what it thinks. It should show what it found, how it interpreted it, how important it appears to be, how confident it is, and where the original evidence came from.**
