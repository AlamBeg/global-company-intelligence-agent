# Implementation Status

This documents what actually runs today, as of 2026-09-06, separate from the
aspirational scope in `PRODUCT_REQUIREMENTS.md`. Treat this file as the
source of truth for "does X work" — if it's not listed here as built, it
isn't wired yet, regardless of what the PRD describes.

## What's built, tested, and live-verified

**21 tests passing** (`pytest`, `tests/`), including a full end-to-end
integration test (`test_end_to_end.py`) that runs the real pipeline against
a fixture and asserts on the API response, not just internal function
returns. Also manually verified against a running server (`uvicorn`) with
real HTTP calls via `curl`, not just `TestClient`.

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

**Impact** (`agents/lane2/impact.py`) is coded (a configurable weighted
formula) but **not wired** to storage or any runner — it needs
author-influence and reach signals this MVP doesn't track yet.

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
- Dashboard at `/dashboard` — dark-themed UI covering all of the above,
  including an "Ask" panel and an API-key input for RBAC.

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

- **No live LLM verification**: the provided Anthropic API key returned
  `credit balance too low` — everything above has only been exercised
  through the documented placeholder path (`MockProvider`), never against a
  real model response. The code path is identical either way (same
  `ModelGateway.complete()` call), but "the JSON parses and scores look
  sane" has not been confirmed against actual Claude output. Add billing
  credits, uncomment `ANTHROPIC_API_KEY` in `.env`, and re-run
  `gcia.ingestion.run_ingestion` / `gcia.workflows.run_company_window` to
  verify this.
- **That API key should be rotated** — it was pasted into a chat session.
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
3. Wire `ImpactAgent` once reach/engagement signals are richer (currently
   only Reddit's `score`/`num_comments` are captured; RSS has none).
4. Add a third connector from a genuinely different class (e.g. a review
   site or forum) to further stress-test the `Connector` protocol.
5. PDF/slide briefing export.
