# Code layout

This implements the design in `docs/MULTI_AGENT_ARCHITECTURE.md` ("Execution
model"). Read that first — this file is just a map from that design to files.

```
gcia/
  common/            RunContext, Budget, the Agent interface, ModelGateway
  schemas/           Canonical typed objects (Company, Discussion, Evidence, ...)
  agents/
    lane1/           Streaming, per item: normalization, language, relevance,
                      sentiment, emotion, intent, claim, geography
    lane2/           Batch, per company/window: dedup, topic, narrative,
                      impact, credibility, trend, risk
    lane3/           On-demand, per query: discovery, verification, synthesis
  connectors/        Source connectors (Connector protocol + one RSS example)
  ingestion/         Lane 1 runner (in-process reference; Kafka/Redpanda in production)
  workflows/         Lane 2 runner (in-process DAG; Temporal-class engine in production)
  api/               Lane 3 FastAPI surface (company, evidence, compare, briefing)
```

## Model tiering

Every agent declares a `tier` (`ModelTier.NONE | SMALL | LARGE`, in
`common/agent.py`). `NONE` agents never call an LLM. `SMALL`/`LARGE` agents
call `context.model_gateway.complete(...)` — never the Anthropic SDK
directly — so cost, caching, and model swaps stay in one place
(`common/model_gateway.py`). See `agents/lane1/relevance.py` for the
escalate-on-low-confidence cascade pattern.

## Running locally

```bash
pip install -e ".[dev]"
cp .env.example .env   # fill in ANTHROPIC_API_KEY for real model calls; optional otherwise
pytest
uvicorn gcia.api.main:app --reload
```

The test suite runs entirely against `MockProvider` — no API key or network
access required. `docker-compose.yml` brings up local Postgres/Redis for
when you outgrow SQLite; it does not include Kafka/OpenSearch/a vector
store/Temporal yet — those get added when Lane 1/2 outgrow the in-process
runners (see `ingestion/stream_worker.py` and `workflows/runner.py`
docstrings for the swap points).

## End-to-end pipeline (what actually runs today)

```bash
# Lane 1: connector -> normalize -> relevance -> sentiment -> SQLite
python -m gcia.ingestion.run_ingestion \
  --company-id acme --company-name "Acme Corp" \
  --connector rss --feed-url <rss-feed-url>

python -m gcia.ingestion.run_ingestion \
  --company-id globex --company-name "Globex Corp" \
  --connector reddit --feed-url https://www.reddit.com/r/technology/new.json

# Lane 2: dedup -> topic clustering -> risk, over what Lane 1 marked relevant
python -m gcia.workflows.run_company_window --company-id acme

# Lane 3 (already live via the API):
curl "http://localhost:8000/v1/companies/acme"
curl "http://localhost:8000/v1/compare?company_ids=acme,globex"
curl -X POST "http://localhost:8000/v1/briefings/acme/export?format=markdown"
```

Without `ANTHROPIC_API_KEY` set, relevance/sentiment/topic/risk calls use a
documented placeholder response instead of failing — useful for developing
against the pipeline shape, but not real analysis. A warning is logged every
time this path is taken.

## Access control

Set `GCIA_API_KEYS="key:role,..."` in `.env` (roles: `viewer`, `analyst`,
`admin`) to turn on RBAC (NFR-011), enforced in `common/auth.py` via a
FastAPI dependency on each route. Leaving it empty is a local-dev
convenience (everything resolves to `admin`) — set it before exposing the
API beyond localhost. `/v1/companies/*` requires `viewer`+; evidence,
compare, and briefing export require `analyst`+.
