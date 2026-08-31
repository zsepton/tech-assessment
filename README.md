# Churn Risk & Retention Console

A management console for a retention team: it surfaces which customers are
at risk of churning, explains why, and lets an agent record what they did
about it. Built for the technical assessment described in
[`tech-assessment.md`](tech-assessment.md).

- **Backend**: FastAPI (Python), in-memory data store loaded from the
  bundled CSV at startup (no database).
- **Frontend**: Vite + React + TypeScript, talking to the backend over HTTP.
- **"Model"**: a weighted heuristic, not a trained ML model (per the
  assessment's explicit scope); see [Data modeling & risk
  scoring](#data-modeling--risk-scoring).

## Quick start

Two terminals, from a clean clone. Verified end-to-end (dependency install
through both test suites passing) in well under 5 minutes.

**Backend** (Python 3.12+):

1. Create the venv and install dependencies:

   ```bash
   cd backend
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
   ```

2. Run the tests (100%-coverage gate configured in `backend/pyproject.toml`),
   then open the generated coverage report (gitignored build artifact,
   only exists after you run this):

   ```bash
   .venv/bin/pytest
   python3 -m webbrowser htmlcov/index.html
   ```

3. Run the API:

   ```bash
   .venv/bin/uvicorn app.main:app --reload
   ```

   Runs at `http://localhost:8000`. Interactive API docs at
   `http://localhost:8000/docs`.

**Frontend** (Node 20+), in a second terminal:

1. Install dependencies:

   ```bash
   cd frontend
   npm install
   ```

2. Run the tests, then open the generated coverage report (gitignored
   build artifact, only exists after you run this):

   ```bash
   npm run test:coverage
   python3 -m webbrowser coverage/index.html
   ```

3. Run the dev server:

   ```bash
   npm run dev
   ```

   Runs at `http://localhost:5173` and talks to the backend at the URL in
   `frontend/.env` (`VITE_API_BASE_URL`, defaults to `http://localhost:8000`.
   Override it if your backend runs elsewhere).

Open `http://localhost:5173`. You should see the customer dashboard,
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
.pre-commit-config.yaml        # ruff, eslint, pytest-cov, vitest-cov, all gated on 100% coverage
```

## Design choices

Every major technology and architecture decision below was made against
this assessment's actual requirements, not by default. Where a real
alternative existed, it's named along with why it lost.

**Backend: FastAPI.** Three of its built-in features map directly onto
this assessment's actual requirements rather than being generic pluses:
Pydantic models double as request/response validation (400s and 422s
essentially come for free), the async-first design satisfies requirement
#8 (I/O-bound work handled efficiently: the CSV load runs via
`asyncio.to_thread` off the event loop), and the auto-generated OpenAPI
docs (`/docs`) directly serve the "clone and run in 5 minutes" and
`/model/info` introspection goals. Chosen over Flask (would need
marshmallow/Pydantic and a docs library bolted on for the same story) and
Django REST Framework (its ORM, admin site, and migrations are all dead
weight given there's deliberately no database). **Trade-off**: FastAPI's
ecosystem and hiring pool are smaller than Django's, and async-first means
any accidentally-blocking call in a route (a sync file read, a CPU-bound
loop) stalls the whole event loop instead of just one thread; this project
avoids that by keeping the one blocking operation (the CSV load) in
`asyncio.to_thread`.

**Data store: in-memory, loaded from CSV, no database.** The dataset is a
static ~7k rows with exactly one mutable field (`outreach_status`);
standing up Postgres/SQLite would add a migration story and a connection
pool for data that fits comfortably in a Python dict. This is also
explicitly named in the assessment's "Explicitly Out of Scope" section, so
it's the specified scope, not a shortcut. **Trade-off**: every outreach
update is lost on process restart, and a second `uvicorn` worker would
have its own independent copy of the data instead of a shared source of
truth; both are fine for a single-process assessment app but would be the
first thing to fix for anything resembling production use. More in
[Trade-offs and things cut for time](#trade-offs-and-things-cut-for-time).

**Frontend: Vite + React + TypeScript.** This is a pure client-side SPA
talking to a separately-running API. Chosen over Next.js, whose main
value-adds (SSR, file-based routing, API routes) are irrelevant here and
would blur the "genuine separate client" boundary the assessment asks for,
and over Create React App / a hand-rolled webpack config (CRA is
deprecated upstream; hand-rolling would spend setup time on build tooling
instead of features). Vite gives a fast dev server (native ESM, no
bundling in dev) with a minimal, current scaffold. TypeScript over plain
JS because the API client (`src/api/`) and the outreach transition table
are exactly the kind of "shape must match the backend" code where a typo
should be a compile error, not a bug a retention agent finds at runtime.
**Trade-off**: a pure client-side SPA means a blank page until the JS
bundle loads and fetches data (no SSR, no meaningful content for a
crawler); irrelevant for an internal retention tool behind a login, but a
real cost if this were ever public-facing.

**Pagination and filtering: both server-side, never fetch-everything-and-
filter-in-the-browser.** `GET /customers` accepts risk tier, contract, and
outreach status as query params and applies them before paginating, so the
frontend only ever receives the one page of rows that actually match;
`DashboardView` never holds the full ~7k-row dataset in memory just to
slice it client-side. This keeps "what counts as a match" defined in
exactly one place (the backend) instead of two copies of filter logic
drifting between languages, and means the page stays fast and the payload
stays small regardless of how large the underlying dataset grows.

Pagination itself is offset/limit, not cursor-based. Cursor pagination
earns its keep on large or actively-mutating datasets, where stable pages
under concurrent inserts matter; neither applies here (~7k static rows,
only `outreach_status` ever mutates). Offset/limit is trivial with Python
slicing and maps directly onto the numbered Prev/Next pages UI a retention
agent actually wants, rather than an opaque cursor token. **Trade-off**:
offset pagination can skip or repeat a row if the underlying data changes
between page loads (an insert shifts every later offset by one) and gets
slower at very large offsets since the server still has to slice past
everything before the page. Neither matters at ~7k static rows, but both
are the reason cursor pagination exists for datasets that don't fit this
profile.

**UI updates: pessimistic, not optimistic.** The outreach `PATCH` is
exactly the kind of write where showing a false-positive success and then
silently reverting it on a failed request would damage a retention agent's
trust in the tool more than a short, honest wait would. The control
disables itself and shows a pending state until the server confirms the
transition, then renders from the response; on failure it shows the error
state and leaves the prior status untouched instead of rolling back an
already-applied local change. **Trade-off**: the UI feels a full
round-trip slower than optimistic updates would, since the badge only
changes after the server responds; acceptable for an occasional
low-frequency action like recording outreach, but the wrong choice for a
high-frequency interaction where perceived responsiveness matters more
than avoiding a rare visible rollback.

**Linting & type-checking.** Backend: Ruff for lint + format + import
sorting in one tool with near-zero config, plus mypy in `strict` mode,
both set up before any feature code existed so they apply from the first
commit instead of fighting lint debt later. Frontend: ESLint (flat config)
with `typescript-eslint` and `eslint-plugin-react-hooks`, plus Prettier,
chosen over Biome/oxlint (the current Vite template default) because their
React-hooks rule coverage is still less mature, and catching stale-closure
and missing-dependency bugs matters more here than raw lint speed at this
codebase's size. **Trade-off**: ESLint's flat-config setup and plugin
ecosystem is more config surface than Biome's single-binary, near-zero-config
approach, and ESLint is measurably slower on larger codebases (irrelevant
here); mypy `strict` mode also means every function needs full type
annotations, which is upfront friction on some quick helper code.

**Testing bar: 100% line/branch coverage, both sides.** Stricter than the
rubric's stated minimum (scoring logic + state-machine transitions + one
endpoint), chosen over just meeting that minimum, enforced by pre-commit
rather than left to CI or manual discipline.

**Structured JSON logging, error handling via middleware, not an exception
handler.** Every request logs one JSON object instead of a formatted
sentence, chosen over plain-text logging because a log aggregator can
filter on `status_code=500` or compute p99 latency without regex-parsing
a sentence. A `@app.exception_handler(Exception)` looked like the obvious
way to produce the 500 response, but FastAPI's exception-handling layer
sits *inside* user-added middleware: a handler registered on `app` would
intercept the exception before the logging middleware ever saw it,
silently defeating the logging. The middleware itself catches, logs the
traceback, and returns the 500 instead. **Trade-off**: every unhandled
exception collapses to the same generic `{"detail": "Internal server
error"}` regardless of cause, since the middleware can't easily
distinguish exception types the way per-route `@app.exception_handler`
registrations could; fine for a 500 (the client shouldn't see internals
anyway), but it means adding a new handled-error type later means editing
the route to raise a proper `HTTPException` rather than adding a handler.

**Outreach state machine: explicit transition table, duplicated
client-side.** `NOT_CONTACTED → IN_PROGRESS → RESOLVED` is validated
server-side on every `PATCH` against an explicit table, not an ad hoc
if/else, with same-status "transitions" and reopening a `RESOLVED` case
both deliberately illegal. The frontend keeps its own small copy of the
table purely to decide which buttons to offer, chosen over fetching the
table from an endpoint (the way `/model/info` exposes scoring weights);
the backend remains the actual authority regardless of what the frontend
shows. **Trade-off**: the client-side copy can silently drift from the
backend if the state machine changes and the frontend isn't updated in
the same change; the backend still rejects any illegal transition
regardless, so drift shows up as "the UI offered a button that then
errored," not as a real data-integrity problem. See [Trade-offs and things
cut for time](#trade-offs-and-things-cut-for-time) for when duplicating
this stops being reasonable at all.

## Data modeling & risk scoring

`backend/app/services/scoring.py` implements the heuristic. Every weight
and threshold is a named module-level constant. This isn't just tidiness,
it's specifically so `GET /model/info` can return the real rules directly
by importing them, rather than the frontend's "why" explanation being
disconnected from what the backend actually computed.

**Factors and weights** (summed additively, then clamped to 0–100):

| Factor | Weight | Rationale |
|---|---|---|
| Contract: Month-to-month | +30 | Strongest signal: the customer can leave with no penalty at any time, unlike a fixed-term contract. |
| Contract: One year | +10 | Some residual risk vs. a two-year commitment, but far less than month-to-month since leaving early still has a cost. |
| Tenure ≤ 5 months | +25 | Brand-new customers churn most: they haven't yet built up the switching-cost/habit that keeps longer-tenured customers around. |
| Tenure 6–11 months | +15 | Bucketed, not linear: still in the high-risk early window, but the drop-off from new to 6mo is much steeper than from 12mo to 24mo. |
| Tenure 12–23 months | +5 | Past the steepest risk window but not yet long-tenured; a small residual amount of risk remains before loyalty fully sets in. |
| Payment: Electronic check | +15 | Established secondary signal in this dataset: correlates with a less "locked in" relationship than autopay methods (credit card/bank transfer). |
| Tech support: none | +10 | No tech support means service friction goes unresolved instead of being smoothed over, a known churn driver. |
| Online security: none | +8 | Same logic as tech support (an unresolved-friction / lower-engagement add-on), but a weaker secondary signal in this dataset. |
| Paperless billing: yes | +4 | Weak secondary signal in this dataset; a small residual correlation with a more price-sensitive, less-engaged segment. |
| Senior citizen | +5 | Weak secondary signal in this dataset, kept small since it's a demographic rather than a behavioral indicator. |
| Monthly charges elevated vs. billing history | +8 | Signals a recent price increase, a real churn trigger; see the exact definition below the table. |

The "MonthlyCharges/TotalCharges ratio" factor (named in the assessment) is
interpreted as: does the customer's current monthly rate imply they've
historically been charged *less* than their tenure predicts (a >10%
shortfall)? That signals a recent price increase (a real churn trigger)
rather than the raw ratio, which mostly just re-encodes tenure.

**Tiers**: High ≥ 70, Medium ≥ 40, else Low.

**Validation against real data**: all factors here are risk-*increasing* by
construction (none of the assessment's named fields naturally reduce risk,
so no protective factors are modeled). To sanity-check the heuristic isn't
arbitrary, I scored all 7,043 real customers and compared against the
dataset's actual `Churn` label: customers who churned average a score of
**67.4**; customers who stayed average **34.2**, a 33-point separation.

**Outreach state machine** (`services/outreach.py`):
`NOT_CONTACTED → IN_PROGRESS → RESOLVED`, explicit transition table,
RESOLVED terminal (no reopen: nothing in the assessment calls for
revisiting a resolved case). Same-status "transitions" are deliberately
illegal too, not treated as a no-op. Validated server-side on every
`PATCH`; the frontend (`src/outreachTransitions.ts`) mirrors the same table
purely so the UI only *offers* legal buttons; the backend remains the
actual authority regardless of what the frontend offers.

## API design

- `GET /customers`: offset/limit pagination (default 20, capped at 100),
  filters for risk tier / contract / outreach status, sorted by risk score
  descending with customer_id as an explicit tiebreaker (deterministic
  pages, not incidental dict-order).
- `GET /customers/{id}`: full record + risk score + factor breakdown.
- `PATCH /customers/{id}/outreach`: validates the transition before
  mutating anything; the write is a single synchronous dict assignment with
  no `await` between the check and the write.
- `GET /model/info`: the scoring engine's live constants.

**Pagination and filtering** are both server-side, offset/limit rather
than cursor-based; see [Design choices](#design-choices) for the full
reasoning and known weaknesses at larger scale.

## Error handling & logging

**Backend status codes**: every response uses a meaningful HTTP status
code, not a blanket 200/500 split: 400 for a bad filter value, 404 for an
unknown customer id, 422 for a malformed/missing request body or
out-of-range query param (FastAPI's own Pydantic validation, left as its
idiomatic default since the assessment's 400 requirement is scoped to
*filter values*, not basic type/range validation), 500 for anything
unexpected. Every path returns the same `{"detail": ...}` shape, so the
frontend handles errors uniformly regardless of which endpoint failed.

**Backend unhandled exceptions**: caught by `RequestLoggingMiddleware`
itself, not a `@app.exception_handler` (see [Design
choices](#design-choices) for why that would silently defeat the
logging). The middleware logs the full traceback and produces the 500
response from that same place, so an error can never end up logged but
unhandled, or handled but unlogged.

**Logging**: every request logs one JSON object (`timestamp`, `level`,
`method`, `path`, `status_code`, `duration_ms`) instead of a formatted
sentence, so a log aggregator can filter on `status_code=500` or compute
p99 latency without regex-parsing. Level is controlled by `LOG_LEVEL`
(default `INFO`). Output goes to the console only (`logging.StreamHandler`,
i.e. stderr), not to a file: reasonable for an assessment app that runs in
a foreground terminal, where the goal is structured *lines* a log
aggregator could consume, not an actual production log pipeline. A real
deployment would ship stderr to whatever log aggregator the platform
already provides (e.g. a container runtime's log driver) rather than
writing to disk directly.

**Frontend**: `apiRequest()` (`src/api/client.ts`) is the single place
every network call goes through, and it normalizes every failure mode, a
network error with no response at all, a non-2xx HTTP response, and an
unparsable response body, into one `ApiError` type carrying an HTTP status
(`null` for a pure network failure) and a human-readable `detail` string.
FastAPI's 422 validation-error array is flattened into one readable string
here rather than left as raw JSON for a view to unpack. Every calling view
catches exactly this one error type and never has to branch on fetch
mechanics itself.

Failures are surfaced with `ErrorBanner`, not a silent `console.error` or a
blank screen: `DashboardView` and `CustomerDetailView` both show it on a
failed initial load, and `OutreachControl` shows an inline error on a
failed `PATCH` without discarding the customer's current (still-accurate)
status. Every data-fetching effect also guards against race conditions
with a `cancelled` flag set on cleanup, so a component that unmounts (or
whose route param changes) while a request is in flight never calls
`setState` from a stale, superseded response, an explicit scenario covered
in both views' test suites.

## Testing approach

**Both backend and frontend are held to 100% line/branch coverage**,
enforced by pre-commit. See [Design choices](#design-choices) for why this
bar was chosen over the rubric's stated minimum, and the trade-off that
comes with it.

- **Backend** (`pytest --cov=app --cov-fail-under=100`): every module has
  boundary-case and both-branch coverage: every scoring factor's
  trigger/non-trigger case, every legal *and* illegal outreach transition
  (parametrized over all 9 pairs, not spot-checked), every endpoint's happy
  and error paths.
- **Frontend** (`vitest run --coverage`, v8 provider, 100% thresholds):
  every component in isolation plus integration tests wiring them together
  (e.g. clicking an outreach button in the detail view actually updates the
  displayed badge, not just in a unit test of the button alone). Race
  conditions are explicitly tested too: a stale response/rejection that
  resolves *after* a newer request has superseded it is asserted to be
  ignored, exercising the effects' cleanup-based cancellation guards.
- **What's deliberately not covered**: no browser/e2e test suite (no
  Playwright/Cypress); everything above is unit/integration-level.
  Multiple real-backend integration checks were run manually during
  development (a script calling the actual frontend client against a live
  `uvicorn` instance, unmocked) to catch integration bugs the mocked tests
  can't, but these aren't part of the automated/CI-equivalent suite.

## Linting & pre-commit

- **Backend**: Ruff (lint + format + import sort, one tool, near-zero
  config) + mypy (`strict = true`).
- **Frontend**: ESLint (flat config, `typescript-eslint` +
  `eslint-plugin-react-hooks`) + Prettier, chosen over Biome/oxlint; see
  [Design choices](#design-choices) for why, and the trade-off it costs.
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
  caching layer, no deployment/Docker setup.** All explicitly out of
  scope per the assessment's "Explicitly Out of Scope" section, not
  oversights.
- **Outreach state machine duplicated client-side.** The frontend has its
  own small copy of the transition table (to know which buttons to show)
  rather than fetching it from an API. Reasonable here because it's a
  fixed 3-state flow and the backend still validates independently either
  way, but a larger app would want a single source of truth exposed via
  an endpoint the way `/model/info` does for scoring weights.
- **Skeleton loading states are hand-built**, not driven by a library.
  Reasonable at this scale (two skeleton shapes total), would look
  different with many more distinct loading layouts.

## With more time

- Add a real component sheet / visual regression check. Everything here
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
