# Churn Risk & Retention Console

A management console for a retention team: it surfaces which customers are
at risk of churning, explains why, and lets an agent record what they did
about it. Built for the technical assessment described in
[`tech-assessment.md`](tech-assessment.md).

- **Backend**: FastAPI (Python), in-memory data store loaded from the
  bundled CSV at startup — no database.
- **Frontend**: Vite + React + TypeScript, talking to the backend over HTTP.
- **"Model"**: a weighted heuristic, not a trained ML model (per the
  assessment's explicit scope) — see [Data modeling & risk
  scoring](#data-modeling--risk-scoring).

## Quick start

Two terminals, from a clean clone. Verified end-to-end (dependency install
through both test suites passing) in well under 5 minutes.

**Backend** (Python 3.12+):

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload
```

Runs at `http://localhost:8000`. Interactive API docs at
`http://localhost:8000/docs`.

**Frontend** (Node 20+), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173` and talks to the backend at the URL in
`frontend/.env` (`VITE_API_BASE_URL`, defaults to `http://localhost:8000` —
override it if your backend runs elsewhere).

Open `http://localhost:5173` — you should see the customer dashboard,
sorted by risk score, highest first.

## Repository structure

```
data/                          # bundled Telco Customer Churn CSV
backend/
  app/
    main.py                    # FastAPI app, CORS, lifespan (CSV load), middleware wiring
    routes/                    # customers.py (list/detail/outreach), model_info.py
    models/                    # Pydantic schemas (Customer, RiskScore, CustomerDetail, ...)
    services/                  # scoring.py (heuristic engine), outreach.py (state machine)
    data_access/               # CSV loader, in-memory store
    middleware/                # structured request-logging middleware
    logging_config.py          # JSON log formatter, LOG_LEVEL env var
  tests/                       # pytest, one file per module/endpoint, 100% coverage
  pyproject.toml                # ruff, mypy, pytest/coverage config
frontend/
  src/
    views/                    # DashboardView, CustomerDetailView
    components/               # RiskBadge, OutreachControl, FilterBar, Pagination, skeletons, ErrorBanner
    api/                      # typed fetch client (types.ts, client.ts, customers.ts, modelInfo.ts)
    outreachTransitions.ts    # frontend mirror of the backend's outreach state machine
  vite.config.ts               # Vitest config (jsdom, v8 coverage, 100% thresholds)
.pre-commit-config.yaml        # ruff, eslint, pytest-cov, vitest-cov — all gated on 100% coverage
```

## Framework choices

**Backend — FastAPI.** Three of its built-in features map directly onto
this assessment's actual requirements rather than being generic pluses:
Pydantic models double as request/response validation (400s and 422s
essentially come for free), the async-first design satisfies requirement
#8 (I/O-bound work handled efficiently — the CSV load runs via
`asyncio.to_thread` off the event loop), and the auto-generated OpenAPI
docs (`/docs`) directly serve the "clone and run in 5 minutes" and
`/model/info` introspection goals. Flask/Django REST would need extensions
bolted on for the same validation/docs story, and Django's ORM/admin/
migrations are all dead weight given there's deliberately no database.

**Frontend — Vite + React + TypeScript.** This is a pure client-side SPA
talking to a separate API — Next.js's main value-adds (SSR, file-based
routing, API routes) are irrelevant here and would blur the "genuine
separate client" boundary the assessment asks for. Vite gives a fast dev
server and a trivial scaffold with none of Next's unused SSR machinery or
vanilla React's hand-rolled build config.

## Data modeling & risk scoring

`backend/app/services/scoring.py` implements the heuristic. Every weight
and threshold is a named module-level constant — this isn't just tidiness,
it's specifically so `GET /model/info` can return the real rules directly
by importing them, rather than the frontend's "why" explanation being
disconnected from what the backend actually computed.

**Factors and weights** (summed additively, then clamped to 0–100):

| Factor | Weight | Rationale |
|---|---|---|
| Contract: Month-to-month | +30 | Strongest signal — no penalty for leaving |
| Contract: One year | +10 | Some residual risk vs. a two-year commitment |
| Tenure ≤ 5 months | +25 | Brand-new customers churn most |
| Tenure 6–11 months | +15 | Bucketed, not linear — the drop-off from new to 6mo is much steeper than 12mo to 24mo |
| Tenure 12–23 months | +5 | |
| Payment: Electronic check | +15 | Established secondary signal in this dataset |
| Tech support: none | +10 | |
| Online security: none | +8 | |
| Paperless billing: yes | +4 | |
| Senior citizen | +5 | |
| Monthly charges elevated vs. billing history | +8 | See below |

The "MonthlyCharges/TotalCharges ratio" factor (named in the assessment) is
interpreted as: does the customer's current monthly rate imply they've
historically been charged *less* than their tenure predicts (a >10%
shortfall)? That signals a recent price increase — a real churn trigger —
rather than the raw ratio, which mostly just re-encodes tenure.

**Tiers**: High ≥ 70, Medium ≥ 40, else Low.

**Validation against real data**: all factors here are risk-*increasing* by
construction (none of the assessment's named fields naturally reduce risk,
so no protective factors are modeled). To sanity-check the heuristic isn't
arbitrary, I scored all 7,043 real customers and compared against the
dataset's actual `Churn` label: customers who churned average a score of
**67.4**; customers who stayed average **34.2** — a 33-point separation.

**Outreach state machine** (`services/outreach.py`):
`NOT_CONTACTED → IN_PROGRESS → RESOLVED`, explicit transition table,
RESOLVED terminal (no reopen — nothing in the assessment calls for
revisiting a resolved case). Same-status "transitions" are deliberately
illegal too, not treated as a no-op. Validated server-side on every
`PATCH`; the frontend (`src/outreachTransitions.ts`) mirrors the same table
purely so the UI only *offers* legal buttons — the backend remains the
actual authority regardless of what the frontend offers.

## API design

- `GET /customers` — offset/limit pagination (default 20, capped at 100),
  filters for risk tier / contract / outreach status, sorted by risk score
  descending with customer_id as an explicit tiebreaker (deterministic
  pages, not incidental dict-order).
- `GET /customers/{id}` — full record + risk score + factor breakdown.
- `PATCH /customers/{id}/outreach` — validates the transition before
  mutating anything; the write is a single synchronous dict assignment with
  no `await` between the check and the write.
- `GET /model/info` — the scoring engine's live constants.

**Pagination: offset/limit, not cursor-based.** Cursor pagination earns its
keep on large or actively-mutating datasets (stable pages under concurrent
inserts) — neither applies here (~7k static rows, only `outreach_status`
ever mutates). Offset/limit is trivial with Python slicing and maps
directly to the numbered-pages UI a retention agent actually wants.

**Errors**: 400 for a bad filter value, 404 for an unknown customer, 422
for a malformed/missing request body or out-of-range query param (FastAPI's
own Pydantic validation — deliberately left as its idiomatic default rather
than forced into 400, since the assessment's 400 requirement is scoped to
*filter values*, not basic type/range validation), 500 for anything
unexpected. Every path returns the same `{"detail": ...}` shape.

**Logging**: genuinely structured, not just formatted text — every request
logs one JSON object (`timestamp`, `level`, `method`, `path`, `status_code`,
`duration_ms`), so a log aggregator can filter on `status_code=500` or
compute p99 latency without regex-parsing a sentence. Unhandled exceptions
are logged with full traceback via the same middleware that produces the
500 response (a `@app.exception_handler` would've been the obvious
alternative, but FastAPI's exception-handling layer sits *inside*
user-added middleware — a handler registered on `app` intercepts the
exception before the middleware ever sees it, silently defeating the
logging). Level is controlled by the `LOG_LEVEL` env var (default `INFO`).

## Testing approach

**Both backend and frontend are held to 100% line/branch coverage**,
enforced by pre-commit — stricter than the rubric's stated minimum
(scoring logic + state-machine transitions + one endpoint). This was a
deliberate choice to hold the frontend to the same bar as the backend,
made partway through the build (see the frontend Vitest setup), not an
oversight that it was originally missing.

- **Backend** (`pytest --cov=app --cov-fail-under=100`): every module has
  boundary-case and both-branch coverage — every scoring factor's
  trigger/non-trigger case, every legal *and* illegal outreach transition
  (parametrized over all 9 pairs, not spot-checked), every endpoint's happy
  and error paths.
- **Frontend** (`vitest run --coverage`, v8 provider, 100% thresholds):
  every component in isolation plus integration tests wiring them together
  (e.g. clicking an outreach button in the detail view actually updates the
  displayed badge, not just in a unit test of the button alone). Race
  conditions are explicitly tested too — a stale response/rejection that
  resolves *after* a newer request has superseded it is asserted to be
  ignored, exercising the effects' cleanup-based cancellation guards.
- **What's deliberately not covered**: no browser/e2e test suite (no
  Playwright/Cypress) — everything above is unit/integration-level.
  Multiple real-backend integration checks were run manually during
  development (a script calling the actual frontend client against a live
  `uvicorn` instance, unmocked) to catch integration bugs the mocked tests
  can't, but these aren't part of the automated/CI-equivalent suite.

## Linting & pre-commit

- **Backend**: Ruff (lint + format + import sort, one tool, near-zero
  config) + mypy (`strict = true`).
- **Frontend**: ESLint (flat config, `typescript-eslint` +
  `eslint-plugin-react-hooks`) + Prettier. ESLint over Biome/oxlint
  (the Vite template's current default): both are faster, but their
  React-hooks rule coverage is still less mature, and catching stale-
  closure/missing-dependency bugs matters more here than raw lint speed on
  a codebase this size.
- **Pre-commit** (`.pre-commit-config.yaml`, install with
  `pre-commit install` after the backend venv exists): runs Ruff, ESLint,
  `pytest --cov` (100% required), and `vitest run --coverage` (100%
  required) on staged files, scoped by path so an backend-only commit
  doesn't trigger the frontend hooks and vice versa.

## Trade-offs and things cut for time

- **No caching of computed risk scores.** Every `GET /customers` and
  `GET /customers/{id}` recomputes the heuristic fresh from the in-memory
  CSV data. Fine at ~7k rows with a pure-Python heuristic (sub-second), but
  is the first thing that would need to change if this dataset were 100x
  larger or the "model" were a real ML inference call.
- **No cursor pagination, no real database, no auth, no rate limiting, no
  caching layer, no deployment/Docker setup** — all explicitly out of
  scope per the assessment's "Explicitly Out of Scope" section, not
  oversights.
- **Outreach state machine duplicated client-side.** The frontend has its
  own small copy of the transition table (to know which buttons to show)
  rather than fetching it from an API. Reasonable here because it's a
  fixed 3-state flow and the backend still validates independently either
  way, but a larger app would want a single source of truth exposed via
  an endpoint the way `/model/info` does for scoring weights.
- **Skeleton loading states are hand-built**, not driven by a library —
  reasonable at this scale (two skeleton shapes total), would look
  different with many more distinct loading layouts.

## With more time

- Add a real component sheet / visual regression check — everything here
  was verified via automated tests plus manual API integration scripts,
  but I was not able to get a literal browser-rendered visual check working
  in the sandbox this was built in (see note in each frontend PR).
- Expose the outreach transition table via an API (mirroring
  `/model/info`) instead of duplicating it client-side, so a backend
  change to the state machine can't silently drift from what the frontend
  offers.
- Add e2e tests (Playwright) covering the full list → detail → outreach
  update flow through a real browser, complementing the current unit/
  integration coverage.
- Cache computed risk scores (invalidated on outreach mutation) if the
  dataset or "model" cost grows.
- A numbered-page-jump pagination control (currently Prev/Next only) once
  there's a concrete need to jump far into a large result set.
