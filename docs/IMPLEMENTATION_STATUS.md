# Implementation Status

This documents what actually runs today, as of 2026-09-06, separate from the
aspirational scope in `PRODUCT_REQUIREMENTS.md`. Treat this file as the
source of truth for "does X work" — if it's not listed here as built, it
isn't wired yet, regardless of what the PRD describes.

## What's built, tested, and live-verified

**45 tests passing** (`pytest`, `tests/`), including a full end-to-end
integration test (`test_end_to_end.py`) that runs the real pipeline against
a fixture and asserts on the API response, not just internal function
returns. Also manually verified against a running server (`uvicorn`) with
real HTTP calls via `curl` and against an actual browser (via automation),
not just `TestClient`.

### Real AI analysis is confirmed working (Ollama, local)
Both provided Anthropic and OpenAI API keys authenticate correctly but have
no usable billing on either account. Rather than stay blocked, added
**Ollama** (`agents`/`common/model_gateway.py`'s `OllamaProvider`) as a
third, genuinely free, local model provider — installed on this machine,
`llama3.2` (fast tier) and `llama3.1` (large tier) pulled, and verified with
a real, non-mocked, end-to-end ingestion + Lane 2 run. Real output is
meaningfully differentiated (e.g. an earnings article correctly scored
positive with excitement/pride emotions; a complaints article scored
negative with anger/frustration; an unrelated weather article correctly
excluded as irrelevant) - not the flat "neutral everywhere" placeholder
output every prior verification in this file was limited to.
`GCIA_MODEL_PROVIDER` in `.env` switches provider; switching back to
`anthropic`/`openai` needs no code change once either account has credits.

**Real local-model testing surfaced three genuine bugs, now fixed:**
1. `aspect_sentiment`/`emotions` (typed `dict[str, float]`) crashed the
   pipeline when the local model returned word labels ("positive") instead
   of numbers - fixed with `common/coercion.py`'s `coerce_float_dict`, used
   by both `SentimentAgent` and `EmotionAgent`, plus a clearer prompt.
2. `list_relevant_discussions` joined `RelevanceRecord` to `DiscussionRecord`
   on `discussion_id` alone, not also `company_id` - since discussion_id is
   a content hash, two companies ingesting identical content (as happened
   here: `acme` in placeholder mode and `acme-real` via Ollama both ingested
   the same fixture) could leak one company's relevance judgment into
   another's Lane 2 input. Fixed; regression test in
   `test_relevance_isolation.py`.
3. `get_company_summary`'s sentiment aggregate had the same gap - it wasn't
   filtered by relevance at all, so an irrelevant discussion's leftover
   sentiment (shared cross-company by design, since `SentimentRecord` is
   keyed by content hash alone) could skew the headline sentiment score.
   Fixed with the same join pattern; also regression-tested.

Both bugs were invisible under placeholder mode (every item was neutral, so
nothing looked wrong) and only surfaced once real, differentiated data
existed - a concrete argument for finishing real-provider verification
early rather than developing exclusively against the mock path.

### Entity resolution
`POST /v1/resolve-company` (`agents/entity.py`) resolves a free-text
identifier (name, alias, ticker, domain) to a canonical company via a small
seed registry - deterministic, no LLM call. Unrecognized input resolves to
a new canonical entity (slugified) rather than failing, per FR-001. This was
the one previously-undocumented gap among the 21 agents in
`MULTI_AGENT_ARCHITECTURE.md` - it is now wired.

### Connectors
- **RSS** (`connectors/rss_news.py`) — real XML parsing, tested against a
  fixture and structurally sound for real feeds.
- **Reddit public JSON** (`connectors/reddit_public.py`) — tested against a
  fixture; live network access to `reddit.com` was blocked (HTTP 403) from
  this sandboxed environment specifically — untested against the real
  network, but the connector logic itself is unit-tested and should work
  from a normal machine/network.

### Lane 1 (streaming, per item) — all wired into `ingestion/run_ingestion.py`
Normalization, Language (heuristic placeholder), Geography (keyword
gazetteer placeholder), **Verification** (real HTTP HEAD checks — this one
is genuinely live, not placeholder, since it needs no LLM), Relevance,
Sentiment, Emotion, Intent, Claim extraction. All LLM-backed agents fall
back to a documented placeholder response when `ANTHROPIC_API_KEY` is
unset, with a logged warning — this was exercised throughout since a real
key was blocked by an account billing issue (see "Known blockers" below).

### Lane 2 (batch, per company/window) — all wired into `workflows/run_company_window.py`
Deduplication (shingle+Jaccard placeholder), Topic clustering (naive
word-overlap clustering — placeholder for real embedding clustering),
Narrative clustering, Risk, **Credibility** (partially real: originality and
cross-platform corroboration are computed from actual dedup/engagement
data; the other 5 inputs are a documented neutral placeholder pending
author-history tracking).

**Trend** (`workflows/run_trend.py`) is genuinely computed from real
`collected_at` timestamps (test proves this by backdating rows and
asserting the resulting percentage) — not fabricated. A freshly-ingested,
single-burst dataset will correctly show ~0%/no-baseline, which is the
honest answer for that data shape, not a bug.

**Impact** (`agents/lane2/impact.py`) is now wired into
`run_company_window.py` and persisted as a company-level average. Engagement
(real, from Reddit's `score`/`num_comments` - always 0 for RSS, which has no
engagement metrics), topic_importance (real, cluster size ratio), and
propagation (real, whether the item was echoed elsewhere) are genuine
signals; reach, author_influence, and velocity remain a documented neutral
placeholder pending follower/author-history tracking and multi-window
baselines. Verified live and by test (`test_impact_wiring.py`) that the
result is not the flat placeholder constant.

### Lane 3 (on-demand) — wired into the API
- `GET /v1/companies/{id}` — aggregated summary (sentiment, topics,
  narratives, risks, geography, credibility, dedup stats, evidence with
  original URLs).
- `POST /v1/companies/{id}/ask` — evidence-grounded Q&A (Synthesis agent,
  the "AI Analyst" capability).
- `GET /v1/companies/{id}/trend` — real time-window comparison.
- `POST /v1/companies/{id}/discover-queries` — search-vocabulary expansion
  suggestions (Discovery agent).
- `GET /v1/compare?company_ids=a,b` — side-by-side comparison (FR-031).
- `POST /v1/briefings/{id}/export?format=markdown|json` — executive
  briefing export (FR-032); PDF/slide export is **not built**.
- `GET /v1/evidence/{id}` — raw evidence lookup.
- Dashboard at `/dashboard` — redesigned against a provided reference
  mockup: sidebar nav (only Overview/Ask functional, everything else
  explicitly marked "not built" rather than faked), hero section with
  honest capability facts, real Discussion Sources donut, a real
  interactive choropleth world map (jsvectormap via CDN, colored by actual
  per-country counts - hit and fixed a real library API bug during
  integration, documented in the commit), topic progress bars, a
  platform-filterable evidence feed, a working Compare panel, and the AI
  Analyst Ask panel. Screenshots of the live dashboard:
  `docs/current_dashboard_top.jpg`, `docs/current_dashboard_geo.jpg`,
  `docs/current_dashboard_real_ollama.jpg` (this last one shows real,
  non-placeholder Ollama output).

### Cross-cutting
- **RBAC** (NFR-011): `viewer`/`analyst`/`admin` roles enforced at the API
  layer via `common/auth.py`, configured through `GCIA_API_KEYS`. Verified
  live: no key → 401, insufficient role → 403, sufficient role → 200/normal
  handler response.
- **Storage**: SQLite by default (zero infra), Postgres-ready via
  `DATABASE_URL` + `docker-compose.yml`.
- **Idempotency**: discussion/evidence/claim/topic/risk records are keyed to
  avoid duplicate rows on re-ingestion. Fixed a real bug this session where
  evidence/claim/topic/risk IDs were derived only from `discussion_id`
  (content hash), which silently collided when two different companies
  ingested identical content — now scoped by `company_id` too. Caught by the
  test suite, not by inspection.
- **Model cost tiering**: `ModelGateway` routes SMALL/LARGE tiers, supports a
  confidence-based escalation cascade (`RelevanceAgent`), and caches
  identical calls — all covered by tests.

## Known blockers / honest gaps

- **Anthropic and OpenAI accounts both have no usable credit** - real
  analysis is confirmed working, but only via the local Ollama path, which
  is meaningfully lower quality than either frontier model. Add billing to
  either account and flip `GCIA_MODEL_PROVIDER` to verify with a stronger
  model - no code change needed.
- **All three API keys handled in this session should be rotated** - the
  Anthropic key, the OpenAI key, and (less critically, since it never left
  the local machine) nothing needed for Ollama. All were pasted into a chat
  session at some point.
- Local Ollama inference is slow on CPU (tens of seconds per call) - fine
  for a demo/dev loop, not for any real ingestion volume.
- Only 2 of the "Social platforms" and "News and media" source classes in
  FR-004 exist (RSS, Reddit). No multilingual support, no X/YouTube/TikTok/
  Instagram/Facebook/LinkedIn connectors, no non-English language handling.
- No streaming/continuous ingestion — everything is a one-shot CLI script.
  No scheduler, no Kafka/Redpanda, no Temporal — see the "swap point"
  docstrings in `ingestion/stream_worker.py` and `workflows/runner.py`.
- No knowledge graph, no vector store, no full-text search index — the
  dashboard/API read directly from relational tables.
- Alerting/notifications: explicitly deferred per your instruction.
- No automated evaluation harness (precision/recall/calibration datasets)
  per PRD section 10 — tests check pipeline correctness, not analysis
  quality.

## Recommended next steps, in order

1. Fix the Anthropic billing issue and do one real (non-placeholder) run to
   sanity-check actual model output quality and JSON-parsing robustness
   against real responses (Claude doesn't always return byte-perfect JSON
   even when asked to).
2. Replace the naive word-overlap topic clustering and shingle-based dedup
   with real embedding similarity (needs a vector store).
3. Track real reach/author-influence/follower signals so Impact's remaining
   placeholder inputs (reach, author_influence, velocity) can become real -
   engagement, topic_importance, and propagation already are.
4. Add a third connector from a genuinely different, compliant source class
   (an official review-site or forum API, not ad-hoc scraping - see
   SOURCE_CONNECTORS.md "Compliance") to further stress-test the `Connector`
   protocol.
5. PDF/slide briefing export.
