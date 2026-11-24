# FastAPI + React Refactor

**Date:** 2026-11-23
**Status:** Draft, open questions decided

## Overview

Replace the Streamlit user interface with a Python API (FastAPI) and a React single-page app (Vite, TypeScript). The database, PDF parser, importer and query layer stay in Python and are reused unchanged. The goal is the look and behaviour of the approved Claude Design frames, which Streamlit cannot reproduce closely.

Reference design (Claude Design, private): https://claude.ai/artifact/4SS4TYFyzod4BiA3aNEmid
Frames: Home, Competitions, Figures, Athletes (Overview / Competitions / History), Athletes · History.

---

## Goals

- Pixel-close match to the Claude Design frames: fonts, spacing, tables, tabs, filter rows, split rank pills, struck-through judge marks.
- Keep every behaviour the current pages provide (see the parity checklist below), unless the design explicitly changes it.
- One source of truth for scoring and ranking logic, shared by the API and the tests.
- The existing deployment model (Docker on the NAS, Caddy with basic auth and HTTPS) keeps working.

## Non-goals

- No change to the PDF parser, importer, validation rules or database schema.
- No change to authentication. Caddy basic auth continues to protect the whole site. No user accounts.
- No multi-user editing. The app remains single-writer SQLite.
- No mobile-first redesign. Layout must work at phone width (no horizontal page scroll at 390px), but the target is desktop.

---

## Architecture

```
Browser ──► Caddy (HTTPS + basic auth) ──► app container
                                              ├─ FastAPI  /api/*        (Python)
                                              │     └─ db/, parser/, reuses existing modules
                                              └─ static React build  /  (served by FastAPI)
```

- **Backend:** FastAPI application in a new `api/` package. It imports `db.queries`, `db.importer`, `parser.*` and `ui/`-independent helpers. It must not import Streamlit.
- **Frontend:** React 18 + TypeScript + Vite in a new `web/` directory. Build output goes to `web/dist/`.
- **Single container in production.** FastAPI serves the built frontend for every non-`/api` path (index.html fallback for client-side routes). Caddy keeps routing the whole site to one upstream, so `Caddyfile` changes only the port.
- **Development:** `uvicorn api.main:app --reload` on port 8000, and `npm run dev` on port 5173 with a Vite proxy for `/api`.

### Repository layout (target)

```
api/
  main.py            FastAPI app, static file serving, router registration
  routers/           competitions.py, athletes.py, figures.py, clubs.py, home.py, imports.py
  schemas.py         Pydantic response models
  services/
    scoring.py       trimmed mean, struck flags, rank helpers (moved from ui/components.py)
db/                  unchanged
parser/              unchanged
web/
  src/
    api/             typed client, one function per endpoint
    pages/           Home, Competitions, Figures, Athletes, Clubs, Import
    components/      shared table, pill, tabs, filter row, stat card
    theme/           tokens (colours, type, spacing) taken from the Claude Design frames
  index.html
  package.json
tests/               existing pytest suite + tests/api/ for the new endpoints
```

`ui/` and `views/` are removed once the parity checklist is complete (see Migration).

---

## API

All endpoints are under `/api`, return JSON, and use snake_case keys to match the database columns. Dates are ISO strings (`YYYY-MM-DD`). Missing numeric values are `null`, never `NaN`.

| Method and path | Backed by (existing code) | Purpose |
|---|---|---|
| `GET /api/home?level=` | `competitions_for_level`, `level_athlete_count`, `results_for` | Latest competition summary and totals per level |
| `GET /api/competitions?level=` | `competitions_for_level` | Competitions for a level, one entry per age group |
| `GET /api/competitions/{cc_id}/results` | `results_for` | Results table rows, including `year_of_birth` |
| `GET /api/competitions/{cc_id}/figures` | `competition_figures` | Figure list (number, name, difficulty) |
| `GET /api/competitions/{cc_id}/figure-detail` | `competition_figure_detail` | Judge marks per athlete and figure, with `coefficient` and `figure_score` |
| `GET /api/athletes?q=` | `athlete_list`, `athlete_summaries` | Athlete list with competitions count, best and average score |
| `GET /api/athletes/{id}` | `athlete_history`, `athlete_rankings`, `athlete_overall_ranks` | Profile header data and history |
| `GET /api/athletes/{id}/competitions` | `athlete_rankings`, `athlete_figure_detail` | Competitions tab: per competition overall and by-year ranks, per-figure judge detail and figure ranks |
| `GET /api/athletes/{id}/figures` | `athlete_figure_detail` | History tab: per figure, per competition judge marks |
| `GET /api/figures?level=` | `catalogue_figures` | Figure catalogue with performances count |
| `GET /api/clubs` | `club_list` | Club picker |
| `GET /api/clubs/{id}` | `club_roster`, `club_medals`, `club_avg_scores` | Club roster, medals, average score per competition |
| `POST /api/imports/preview` | `detect_format`, `get_parser`, `validate` | Upload a PDF; return detected format, level, athlete count, errors, warnings. Stores the file in the inbox, keyed by SHA-256 |
| `POST /api/imports` | `import_competition` | Import a previewed file. Errors: `409` already imported, `422` validation failed |

### Scoring and ranking

Rules currently live in `ui/components.py` (`trimmed_flags`, `rank_with_field_size`) and in `parser/validate.py`. They move to `api/services/scoring.py`:

- `trimmed_flags(marks) -> (flags, average)`: drop the single lowest and single highest mark, mean of the rest. Used by the validator as well, so both sides agree.
- The API returns per-mark `dropped` flags. The frontend does not recompute averages or scores; it displays what the API returns.
- Ranks are returned as integers. Adaptive ranking on the Competitions page (renumbering after filters) is done in the frontend, since it depends on the current filter state. The API returns the official rank as `rank` so the grey half of the pill can show it.

---

## Frontend

### Routes

| Route | Page | Current Streamlit equivalent |
|---|---|---|
| `/` | Home | `views/0_home.py` |
| `/competitions` | Competitions | `views/2_competitions.py` |
| `/figures` | Figures | `views/5_figures.py` |
| `/athletes` | Athletes list | `views/3_athletes.py` |
| `/athletes/:id` | Athlete profile (Overview, Competitions, History) | `views/3_athletes.py` |
| `/clubs` and `/clubs/:id` | Clubs | `views/4_clubs.py` |
| `/import` | Import | `views/1_import.py` |

The left navigation matches the Claude Design frames: brand mark, then Home, Competitions, Figures, Athletes, Clubs, and Import (Import is hidden from the nav in the current app and stays reachable at `/import`).

### Design system

- Tokens (colours, font, radii, shadows) come from `ui/theme.py` and the frames: primary `#0E7490`, accent `#5B4BD6`, surface `#F3F6FA`, border `#E2E8F0`, muted `#64748B`, good/bad/neutral rank colours, and dark-mode variants.
- Font: Inter, loaded from Google Fonts.
- Components are plain React with CSS modules using CSS variables. No Tailwind.
- Charts: Recharts (see Decisions). Charts keep current content: positions over time, total score over time, figure scores over time, figure scores per competition, judge marks bar chart (History frames), and the club average line chart.

### Shared behaviour

- **Adaptive rank (Competitions):** rank renumbered 1..n over the rows shown; while any filter is non-empty, the official rank appears in the grey half of the pill.
- **Filters:** text filters match substrings, case-insensitive (name, born, club, country). Range filters accept `min-max`, `min-`, `-max` or an exact value; blank or unparseable input means no filter. Range parsing lives in one utility with unit tests.
- **Empty and loading states:** every table and chart has an explicit empty message from the design ("No results match these filters.", "No figure results for these athletes.").
- **Competitions page:** results and figure detail stay hidden until a competition is selected. Both tables follow the same filtered athlete list.

---

## Parity checklist

Each item must be verified against the current Streamlit page before its view is removed.

- Home: latest competition per level, athlete count, top score.
- Competitions: level switch, competition and age group selection, results table with sort and filters, figure list, figure detail. Design changes apply: no age group selector, filter row, adaptive rank, figure detail table without the judge detail expander.
- Figures: level selector, catalogue table (code, name, coefficient, description, performances, competitions).
- Athletes: search, selection, header stats, Overview (history table, total score chart, positions chart), Competitions (overall or by-year switch, one tab per competition, figure table with struck marks, average, score, rank), History (one tab per figure with judge bar chart and trimmed average markers).
- Clubs: club picker, roster, medals, average score line chart.
- Import: upload one or more PDFs, detected format with manual override, parse and validation report, import button, duplicate and failure messages.

---

## Migration

1. **Phase 0 (foundation):** `api/` skeleton with `/api/health`, `services/scoring.py` moved and tested, Vite app with routing, tokens, and the nav shell. Streamlit still runs from `app.py`.
2. **Phase 1 (read-only pages):** Home, Competitions, Figures, Athletes, Clubs, one per PR, each with its API routes, API tests and React page. Streamlit pages stay until each is at parity.
3. **Phase 2 (import):** the preview and import endpoints and the Import page, including the file-picking flow.
4. **Phase 3 (cutover):** remove `app.py`, `views/`, `ui/`, the Streamlit dependency, and Streamlit tests in `tests/test_pages_smoke.py`. Update `Dockerfile`, `docker-compose.yml` and `Caddyfile` to the single FastAPI container. Update `docs/deployment.md`.

Each phase ends with a working app and a passing test suite.

---

## Testing

- **Backend:** pytest with FastAPI's `TestClient`. Each router gets tests against the seeded database used by the current tests (`seeded_app_db`, `conn` fixtures). Parser, importer, validation and query tests stay as they are.
- **Scoring:** `services/scoring.py` has the existing trimmed-mean and rank tests, moved with the code.
- **Frontend:** Vitest for utilities (range parsing, adaptive rank, filter matching) and component tests for the table, pill and tabs.
- **End to end:** Playwright smoke tests that open each route against a seeded database and check the key elements from the parity checklist.
- **Visual:** screenshots of each page at 1280px and 390px, compared by eye against the Claude Design frames before each cutover.

---

## Deployment

- **Dockerfile:** two stages. Stage 1 (`node:24-alpine`) builds `web/dist`. Stage 2 (`python:3.12-slim`) installs `requirements.txt`, copies the API, the Python packages and `web/dist`, and runs `uvicorn api.main:app --host 0.0.0.0 --port 8000`.
- **docker-compose.yml:** the `app` service keeps its volumes (`/data` for the database, `/inbox` for uploads) and environment (`AQUABELY_DB`, `AQUABELY_INBOX`). Only the internal port changes.
- **Caddyfile:** `reverse_proxy app:8000`. Basic auth and HTTPS are unchanged.
- **Requirements:** add `fastapi`, `uvicorn[standard]`, `python-multipart` (for uploads). Remove `streamlit` and `plotly` at cutover. `pdfplumber`, `pandas` and `pytest` stay.

---

## Decisions

1. **Charting library: Recharts.** Covers every chart in the frames (positions, total score, figure scores, judge marks, club averages).
2. **Styling: CSS modules with CSS variables.** Claude Design frames are plain HTML and CSS with CSS variables, so their classes and values port directly. Tailwind would mean rewriting each inline style as utility classes.
3. **Same origin for `/api` in production.** FastAPI serves the React build and the API, so no CORS configuration is needed.
4. **Redirects from old Streamlit paths during cutover:** `/Import`, `/Competitions`, `/Athletes`, `/Clubs`, `/Figures` redirect to their new routes.
5. **Upload size cap: 50 MB**, enforced by the API on `POST /api/imports/preview`.

---

## Acceptance criteria

- Every route in the parity checklist renders with the seeded database and matches its Claude Design frame within the agreed tolerance at 1280px and 390px.
- The API returns the same numbers as the current Streamlit pages for the same database (checked by test for results, rankings, figure detail and club averages).
- Import preview and import reproduce the current behaviour, including duplicate and validation failures.
- `pytest` passes, Playwright smoke tests pass, and the Docker image builds and serves the app behind Caddy with basic auth.
- Streamlit, `views/` and `ui/` are removed, and `docs/deployment.md` describes the new deployment.
