# FastAPI + React Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Streamlit UI with a FastAPI JSON API and a React (Vite, TypeScript) frontend that matches the Claude Design frames, reusing the existing parser, importer and queries.

**Architecture:** FastAPI in `api/` wraps the existing `db/` and `parser/` code and serves the React build from the same container under `/api` and `/`. Frontend in `web/`, CSS modules with CSS variables, Recharts for charts. Phases follow the spec: foundation, read-only pages, import, cutover.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, python-multipart, pytest, httpx (TestClient); Node 20, React 18, TypeScript, Vite, React Router, Recharts, Vitest, Playwright.

**Spec:** `docs/superpowers/specs/2026-11-23-fastapi-react-refactor-design.md`

## Global Constraints

- Backend: Python 3.12; FastAPI; Uvicorn on port 8000 inside the container.
- Frontend: React 18, TypeScript, Vite; CSS modules with CSS variables; no Tailwind.
- Charts: Recharts only.
- Font: Inter, loaded from Google Fonts.
- Same origin: FastAPI serves `web/dist` and `/api`; no CORS.
- All API keys snake_case; missing numbers are `null`, never `NaN`; dates are `YYYY-MM-DD`.
- Upload cap: 50 MB, enforced on `POST /api/imports/preview`.
- Caddy keeps basic auth and HTTPS; upstream becomes `app:8000`.
- Old Streamlit paths redirect during cutover: `/Import`, `/Competitions`, `/Athletes`, `/Clubs`, `/Figures`.
- Database schema, parser and importer are not changed.

## Review Focus

1. Upload over 50 MB → `413` with a JSON error; the inbox gets no file.
2. Range filter text that is junk (`abc`, `--`) is ignored, not an error, on both the server and the client.
3. Athlete with results but no figure detail → profile loads; Competitions tab shows overall rank only; no crash.
4. Missing judge marks or scores → `null` in JSON (never `NaN`, which is invalid JSON); the UI shows an empty cell.
5. Deep link refresh (for example `/athletes/5`) returns the app shell, while an unknown `/api/...` path returns a JSON 404, not the shell.

---

### Task 1: API skeleton, static serving and test harness

**Files:**
- Modify: `requirements.txt`
- Create: `api/__init__.py`, `api/main.py`
- Create: `tests/api/__init__.py`, `tests/api/conftest.py`, `tests/api/test_main.py`

**Interfaces:**
- Produces: `api.main.app` (FastAPI instance). `GET /api/health` → `{"status": "ok"}`. Static fallback serves `web/dist/index.html` for non-API paths when the build exists; otherwise `404` for non-API paths.
- Produces (fixture): `client` in `tests/api/conftest.py` — `TestClient(app)` with `AQUABELY_DB` pointed at a temp database; `seeded_client` uses the `seeded_app_db` fixture from `tests/conftest.py`.

- [ ] **Step 1: Write the failing test**

```python
# tests/api/test_main.py
def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}

def test_unknown_api_path_is_json_404(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and r.headers["content-type"].startswith("application/json")
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/api/test_main.py -v` — Expected: FAIL, `ModuleNotFoundError: api`.

- [ ] **Step 3: Implement**

Add `fastapi`, `uvicorn[standard]`, `python-multipart`, `httpx` to `requirements.txt`. In `api/main.py` create `app = FastAPI()`, register `/api/health`, mount a catch-all that returns `FileNotFoundError`-safe `FileResponse(web/dist/index.html)` for paths not starting with `api/`, and raise `HTTPException(404)` for `api/*`. The `client` fixture sets `AQUABELY_DB` and patches `db.database.DB_PATH` the same way `tests/test_pages_smoke.py` does.

- [ ] **Step 4: Run to verify it passes**

Run: `pytest tests/api -v` — Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add requirements.txt api tests/api
git commit -m "feat(api): add FastAPI skeleton and test client"
```

---

### Task 2: Move scoring rules into `api/services/scoring.py`

**Files:**
- Create: `api/services/__init__.py`, `api/services/scoring.py`
- Modify: `ui/components.py` (delete `trimmed_flags` and `rank_with_field_size` after the move; keep the rest until cutover)
- Create: `tests/api/test_scoring.py` (moved from `tests/test_components.py`)

**Interfaces:**
- Produces: `trimmed_flags(marks: list[float | None]) -> tuple[list[bool], float | None]` — identical behaviour to the current function. Returns `([False]*n, None)` when fewer than three marks are present.
- Produces: `rank_label(rank: int | None, size: int | None) -> str` — `"3 / 24"`, `"3"` when size is missing, `""` when rank is missing.
- Note: `parser/validate.py` keeps its own `sorted(...)[1:-1]` formula. Task 2 adds a test that both agree on the same inputs; the parser is not made to import from `api/`.

- [ ] **Step 1: Write the failing tests**

Move the `trimmed_flags` tests from `tests/test_components.py` into `tests/api/test_scoring.py` importing from `api.services.scoring`. Add:

```python
def test_rank_label_forms():
    assert rank_label(3, 24) == "3 / 24"
    assert rank_label(3, None) == "3"
    assert rank_label(None, 24) == ""

def test_trimmed_mean_matches_validator():
    from parser.validate import validate  # cross-check via a fixture competition is in tests/test_validate.py
    marks = [7.0, 8.0, 6.0, 7.5]
    flags, avg = trimmed_flags(marks)
    assert avg == sum(sorted(marks)[1:-1]) / 2
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/api/test_scoring.py -v` — Expected: FAIL, import error.

- [ ] **Step 3: Implement**

Copy the two functions into `api/services/scoring.py` unchanged in behaviour. Replace the originals in `ui/components.py` with imports from the new module so the Streamlit pages keep working until cutover.

- [ ] **Step 4: Run the full suite**

Run: `pytest -q` — Expected: all tests pass (148 at the start of this branch, plus moved tests).

- [ ] **Step 5: Commit**

```bash
git add api/services ui/components.py tests/api/test_scoring.py tests/test_components.py
git commit -m "refactor: move trimmed mean and rank labels into api/services/scoring"
```

---

### Task 3: Web app scaffold, tokens and navigation shell

**Files:**
- Create: `web/package.json`, `web/tsconfig.json`, `web/vite.config.ts`, `web/index.html`
- Create: `web/src/main.tsx`, `web/src/App.tsx`, `web/src/theme/tokens.css`, `web/src/components/Shell.tsx`, `web/src/components/Shell.module.css`
- Create: `web/src/App.test.tsx`

**Interfaces:**
- Produces: `App` with routes `/`, `/competitions`, `/figures`, `/athletes`, `/athletes/:id`, `/clubs`, `/clubs/:id`, `/import`. Each route renders a placeholder page component named after the page (for example `CompetitionsPage`).
- Produces: `tokens.css` defining `:root` variables from the frames: `--aq-primary #0E7490`, `--aq-accent #5B4BD6`, `--aq-surface #F3F6FA`, `--aq-border #E2E8F0`, `--aq-muted #64748B`, `--aq-text #0F172A`, `--aq-good-bg #DCFCE7`, `--aq-bad-bg #FEE2E2`, `--aq-eq-bg #F3F4F6`, plus dark-mode overrides under `@media (prefers-color-scheme: dark)`. Inter loaded via Google Fonts `<link>` in `index.html`.
- Produces: `Shell` with the left nav in the order Home, Competitions, Figures, Athletes, Clubs (Import reachable at `/import`, not in the nav).
- Vite dev server proxies `/api` to `http://localhost:8000`.

- [ ] **Step 1: Write the failing test**

```tsx
// web/src/App.test.tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { App } from "./App";

test("nav lists the five main pages in order", () => {
  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
  const links = screen.getAllByRole("link").map((a) => a.textContent);
  expect(links.slice(0, 5)).toEqual(["Home", "Competitions", "Figures", "Athletes", "Clubs"]);
});
```

- [ ] **Step 2: Run to verify it fails**

Run (in `web/`): `npm install && npx vitest run` — Expected: FAIL, `App` not found.

- [ ] **Step 3: Implement**

Scaffold with Vite's React-TS template, add `react-router-dom`, `recharts`, `vitest`, `@testing-library/react`, `jsdom`. Implement `App`, `Shell`, placeholder pages and `tokens.css` as listed.

- [ ] **Step 4: Run to verify it passes**

Run: `npx vitest run` — Expected: PASS. Run `npm run build` — Expected: `web/dist/index.html` is produced.

- [ ] **Step 5: Commit**

```bash
git add web
git commit -m "feat(web): scaffold React app with routes, tokens and nav shell"
```

---

### Task 4: Typed API client

**Files:**
- Create: `web/src/api/client.ts`, `web/src/api/types.ts`, `web/src/api/client.test.ts`

**Interfaces:**
- Produces: `apiGet<T>(path: string): Promise<T>` — throws `ApiError` (`status`, `message`) on non-2xx; `apiPostForm<T>(path: string, body: FormData): Promise<T>`.
- Produces in `types.ts`: `Competition`, `ResultRow`, `FigureDetailRow`, `AthleteSummary`, `AthleteProfile`, `FigureHistoryPoint`, `CatalogueFigure`, `ClubSummary`, `ClubDetail`, `ImportPreview`, `ImportResult` — field names exactly as in the API tables in the spec (snake_case). Each type is written once here and reused by every page task.

- [ ] **Step 1: Write the failing test**

```ts
test("apiGet throws ApiError with status on 404", async () => {
  global.fetch = vi.fn(async () => new Response("{}", { status: 404 })) as any;
  await expect(apiGet("/api/nope")).rejects.toMatchObject({ status: 404 });
});
```

- [ ] **Step 2: Run to verify it fails** — `npx vitest run src/api` — Expected: FAIL, module not found.

- [ ] **Step 3: Implement** `client.ts` (thin `fetch` wrapper, JSON parse, `ApiError`) and `types.ts` with the interfaces above.

- [ ] **Step 4: Run to verify it passes** — `npx vitest run src/api` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/api
git commit -m "feat(web): add typed API client"
```

---

### Task 5: Backend routes for Home and Competitions

**Files:**
- Create: `api/schemas.py` (Pydantic models for these endpoints), `api/routers/__init__.py`, `api/routers/home.py`, `api/routers/competitions.py`
- Modify: `api/main.py` (include routers)
- Create: `tests/api/test_competitions.py`, `tests/api/test_home.py`

**Interfaces:**
- `GET /api/home?level=` → `HomeSummary` built from `competitions_for_level`, `level_athlete_count`, `results_for` (latest competition, athlete count, top scorer name and total).
- `GET /api/competitions?level=` → `list[CompetitionEntry]` from `competitions_for_level`: `competition_category_id`, `competition`, `date`, `age_group_label`.
- `GET /api/competitions/{cc_id}/results` → `list[ResultRow]` from `results_for`: `rank`, `name`, `year_of_birth`, `club`, `country`, `total_score`, `penalty`, `points_behind`. Nulls stay null.
- `GET /api/competitions/{cc_id}/figures` → `list[FigureRow]` from `competition_figures`: `number`, `name`, `difficulty`.
- `GET /api/competitions/{cc_id}/figure-detail` → `list[FigureDetailRow]` from `competition_figure_detail`: `athlete`, `rank`, `figure_name`, `coefficient`, `judges` (list of up to 7 floats or null, from `judge_1`…`judge_7`), `dropped` (list of bool, from `trimmed_flags`), `average` (float or null), `figure_score`, `figure_penalty`.

- [ ] **Step 1: Write the failing tests**

```python
def test_results_include_birth_year_and_nulls(seeded_client, seeded_cc_id):
    rows = seeded_client.get(f"/api/competitions/{seeded_cc_id}/results").json()
    assert rows and "year_of_birth" in rows[0]
    assert "NaN" not in seeded_client.get(f"/api/competitions/{seeded_cc_id}/results").text

def test_figure_detail_marks_dropped_extremes(seeded_client, seeded_cc_id):
    rows = seeded_client.get(f"/api/competitions/{seeded_cc_id}/figure-detail").json()
    r = next(r for r in rows if r["judges"] and any(r["dropped"]))
    kept = [j for j, d in zip(r["judges"], r["dropped"]) if j is not None and not d]
    assert r["average"] == pytest.approx(sum(kept) / len(kept))

def test_unknown_competition_is_404(seeded_client):
    assert seeded_client.get("/api/competitions/99999/results").status_code == 404
```

`seeded_cc_id` is a fixture in `tests/api/conftest.py` returning the category id of the seeded competition. The 404 test requires the router to check existence before returning an empty list.

- [ ] **Step 2: Run to verify they fail** — `pytest tests/api/test_competitions.py tests/api/test_home.py -v` — Expected: FAIL, `404` for every route.

- [ ] **Step 3: Implement** the three routers using the query functions listed in Interfaces. Each route calls `get_connection()`, `init_schema()`, runs the query, and closes the connection in a `try/finally`. `figure-detail` builds `judges`, `dropped` and `average` with `trimmed_flags` from `api.services.scoring`. Map NaN to `None` before returning (`df.where(pd.notna(df), None)`).

- [ ] **Step 4: Run to verify they pass** — `pytest tests/api -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api tests/api
git commit -m "feat(api): add home and competitions routes"
```

---

### Task 6: Backend routes for Athletes

**Files:**
- Modify: `api/schemas.py`
- Create: `api/routers/athletes.py`; modify `api/main.py`
- Create: `tests/api/test_athletes.py`

**Interfaces:**
- `GET /api/athletes?q=` → `list[AthleteSummary]`: `id`, `name`, `club`, `year_of_birth`, `competitions`, `best_score`, `avg_score`. Filter on name or club, case-insensitive, substring. Source: `athlete_list` merged with `athlete_summaries`.
- `GET /api/athletes/{id}` → `AthleteProfile`: summary fields plus `history` (rows from `athlete_history`, without `result_id` and `competition_category_id`) and `overall_ranks` (from `athlete_overall_ranks`). `404` if the athlete does not exist.
- `GET /api/athletes/{id}/competitions` → `list[AthleteCompetition]`: per competition (`date`, `competition`, `rank_overall`, `rank_by_year`, `field_size`, `field_size_by_year`) and `figures` (from `athlete_rankings` and `athlete_figure_detail` merged on competition, date and figure name, with `fig_rank_overall`, `fig_rank_by_year`, `fig_field_size`, `fig_field_size_by_year`, `coefficient`, judge marks, `dropped`, `average`, `figure_score`). Empty `figures` when there are no figure results; the competition is still listed.
- `GET /api/athletes/{id}/figures` → `list[FigureHistory]`: per figure name, the points `{date, competition, judges, dropped, average, figure_score}` ordered by date, from `athlete_figure_detail`.

- [ ] **Step 1: Write the failing tests**

```python
def test_athlete_without_figure_detail_still_lists_competitions(seeded_client, athlete_without_figures_id):
    rows = seeded_client.get(f"/api/athletes/{athlete_without_figures_id}/competitions").json()
    assert rows and rows[0]["figures"] == []

def test_athlete_list_search_is_case_insensitive(seeded_client):
    rows = seeded_client.get("/api/athletes?q=ANN").json()
    assert rows and all("ann" in (r["name"] + r["club"]).lower() for r in rows)

def test_unknown_athlete_is_404(seeded_client):
    assert seeded_client.get("/api/athletes/99999").status_code == 404
```

`athlete_without_figures_id` is a new fixture in `tests/api/conftest.py` that imports one result with no `figure_results` rows. Replace the placeholder assertion in the search test with a check that every returned name or club contains the query, case-insensitively.

- [ ] **Step 2: Run to verify they fail** — `pytest tests/api/test_athletes.py -v` — Expected: FAIL, `404`.

- [ ] **Step 3: Implement** the four routes with the existing queries. Keep the rank merge logic from `views/3_athletes.py` (`fig_ranks` merge on competition, date and figure name, with NaN columns when `athlete_rankings` is empty).

- [ ] **Step 4: Run to verify they pass** — `pytest tests/api -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api tests/api
git commit -m "feat(api): add athlete routes"
```

---

### Task 7: Backend routes for Figures and Clubs

**Files:**
- Modify: `api/schemas.py`
- Create: `api/routers/figures.py`, `api/routers/clubs.py`; modify `api/main.py`
- Create: `tests/api/test_figures.py`, `tests/api/test_clubs.py`

**Interfaces:**
- `GET /api/figures?level=` → `list[CatalogueFigure]` from `catalogue_figures`: `code`, `name`, `coefficient`, `description_cs`, `performances`, `competitions`. `level` must be `L3` or `U12`; anything else is `422`.
- `GET /api/clubs` → `list[ClubSummary]` from `club_list`: `id`, `name`.
- `GET /api/clubs/{id}` → `ClubDetail`: `name`, `roster` (from `club_roster`), `medals` (from `club_medals`: `place`, `count`), `avg_scores` (from `club_avg_scores`: `competition`, `date`, `avg_total`). `404` for an unknown club.

- [ ] **Step 1: Write the failing tests**

```python
def test_figures_rejects_unknown_level(seeded_client):
    assert seeded_client.get("/api/figures?level=X").status_code == 422

def test_club_detail_has_roster_and_medals(seeded_client, seeded_club_id):
    body = seeded_client.get(f"/api/clubs/{seeded_club_id}").json()
    assert set(body) >= {"name", "roster", "medals", "avg_scores"}

def test_unknown_club_is_404(seeded_client):
    assert seeded_client.get("/api/clubs/99999").status_code == 404
```

- [ ] **Step 2: Run to verify they fail** — `pytest tests/api/test_figures.py tests/api/test_clubs.py -v` — Expected: FAIL.

- [ ] **Step 3: Implement** the routers. Use a `Literal["L3", "U12"]` query parameter for `level` so FastAPI validates it.

- [ ] **Step 4: Run to verify they pass** — `pytest tests/api -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api tests/api
git commit -m "feat(api): add figures and clubs routes"
```

---

### Task 8: Competitions page (React)

**Files:**
- Create: `web/src/pages/Competitions/CompetitionsPage.tsx`, `CompetitionsPage.module.css`
- Create: `web/src/pages/Competitions/FilterRow.tsx`, `ResultsTable.tsx`, `FigureDetailTable.tsx`, `RankPill.tsx`
- Create: `web/src/lib/filters.ts`, `web/src/lib/filters.test.ts`
- Modify: `web/src/App.tsx` (route `/competitions` renders `CompetitionsPage`)

**Interfaces:**
- `parseRange(text: string): { min: number; max: number } | null` — `"10-20"`, `"10-"`, `"-5"`, `"10"`; blank or unparseable → `null`.
- `filterResults(rows: ResultRow[], filters: Filters): ResultRow[]` — `Filters` has `name`, `born`, `club`, `country` (case-insensitive substring) and `score`, `penalty`, `behind` (range text). Null values fail a range filter.
- `adaptiveRanks(rows: ResultRow[]): { row: ResultRow; position: number }[]` — position is `index + 1`.
- `isFiltered(filters: Filters): boolean`.
- `FilterRow` props: `filters`, `onChange(key, value)`. Placeholders: `Filter` for text, `Min - max` for ranges, `Year` for born.
- `RankPill` props: `position: number`, `official: number | null`, `filtered: boolean`. Colour: 1 green, 2 neutral, 3 red, others plain. When `filtered`, the right half shows `official` in grey and the left half has square inner corners.
- `CompetitionsPage` state: level (`L3`|`U12`), selected `cc_id` (no default), filters. Results and figure detail render only when a competition is selected. Both tables use `filterResults` output.

- [ ] **Step 1: Write the failing tests**

```ts
// web/src/lib/filters.test.ts
test.each([
  ["10-20", { min: 10, max: 20 }],
  ["10-", { min: 10, max: Infinity }],
  ["-5", { min: -Infinity, max: 5 }],
  ["10", { min: 10, max: 10 }],
  ["", null],
  ["abc", null],
])("parseRange(%s)", (input, expected) => {
  expect(parseRange(input)).toEqual(expected);
});

test("adaptiveRanks renumbers over filtered rows", () => {
  const rows = [{ rank: 1 }, { rank: 3 }, { rank: 4 }] as ResultRow[];
  expect(adaptiveRanks(rows.slice(1)).map((x) => x.position)).toEqual([1, 2]);
});

test("filterResults drops rows with null score for a range filter", () => { /* ... */ });
```

Also a component test: `RankPill` with `filtered` true renders two halves and the grey half carries `official`.

- [ ] **Step 2: Run to verify they fail** — `npx vitest run src/lib` — Expected: FAIL.

- [ ] **Step 3: Implement** `filters.ts`, then the components and page. Use the frames' colours and spacing from `tokens.css`. The page fetches `/api/competitions?level=`, `/results`, `/figure-detail` with React Query-style state (plain `useEffect` is fine for this phase).

- [ ] **Step 4: Run and verify** — `npx vitest run` — Expected: PASS. Start the API and Vite, open `/competitions`, select a competition and filter by club — the rank pill halves and figure table follow the filter. Check against the Claude Design Competitions frame at 1280px.

- [ ] **Step 5: Commit**

```bash
git add web
git commit -m "feat(web): build competitions page from design"
```

---

### Task 9: Home and Figures pages (React)

**Files:**
- Create: `web/src/pages/Home/HomePage.tsx`, `HomePage.module.css`
- Create: `web/src/pages/Figures/FiguresPage.tsx`, `FiguresPage.module.css`
- Modify: `web/src/App.tsx`

**Interfaces:**
- `HomePage` calls `GET /api/home?level=` for L3 and U12 selected by a level control. Shows latest competition, athlete count and top scorer. Empty state: "No L3 competitions yet. Use the Import page to add one."
- `FiguresPage` calls `GET /api/figures?level=`; table columns code, name, coefficient, description, performances, competitions. Level control `L3`/`U12`. Empty state: "No figures in the catalogue for this level."

- [ ] **Step 1: Write the failing tests** — render each page with a mocked `apiGet` returning fixture data; assert the table headers and the empty-state message.

- [ ] **Step 2: Run to verify they fail** — `npx vitest run src/pages` — Expected: FAIL.

- [ ] **Step 3: Implement** both pages against the types in `types.ts`.

- [ ] **Step 4: Run to verify they pass** — `npx vitest run` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web
git commit -m "feat(web): add home and figures pages"
```

---

### Task 10: Athletes list and profile (React)

**Files:**
- Create: `web/src/pages/Athletes/AthletesPage.tsx`, `AthleteProfilePage.tsx`, `CompetitionsTab.tsx`, `HistoryTab.tsx`, `OverviewTab.tsx`, and matching `.module.css`
- Create: `web/src/charts/ScoreLine.tsx`, `PositionsChart.tsx`, `JudgeBarChart.tsx`
- Create: `web/src/lib/athleteRanking.ts`, `web/src/lib/athleteRanking.test.ts`
- Modify: `web/src/App.tsx`

**Interfaces:**
- `AthletesPage`: search box (name or club), table with row click → `/athletes/:id`. Columns: Athlete, Club, Competitions, Best score.
- `AthleteProfilePage` tabs: Overview, Competitions, History (URL-independent tab state is fine). Header stat cards: Club, Born, Competitions, Best / average.
- `CompetitionsTab`: Overall / By year buttons (`aria-pressed`); one sub-tab per competition; rank line `Rank overall: n / N` or `Rank by year: n / N`; figure table with struck dropped marks, average, score, rank coloured against the overall rank. Empty figures → "No figure results for this competition."
- `HistoryTab`: one sub-tab per figure; `JudgeBarChart` with competitions on x, one bar per judge, dropped bars hollow, and a trimmed-average marker per competition.
- `PositionsChart` (Overview): overall rank line plus dashed figure rank lines, y-axis reversed.
- `athleteRanking.ts`: `rankLabel(rank, size)`, `overallOrByYear(entry, mode)` returning the rank and size for the active mode.

- [ ] **Step 1: Write the failing tests**

```ts
test("overallOrByYear picks the by-year fields in by-year mode", () => {
  const e = { rank_overall: 2, field_size: 9, rank_by_year: 1, field_size_by_year: 4 } as any;
  expect(overallOrByYear(e, "by-year")).toEqual({ rank: 1, size: 4 });
});
test("rankLabel without size shows the rank only", () => {
  expect(rankLabel(3, null)).toBe("3");
});
```

Component test: `CompetitionsTab` with an athlete that has no figures shows the empty message and the overall rank.

- [ ] **Step 2: Run to verify they fail** — `npx vitest run src/lib src/pages/Athletes` — Expected: FAIL.

- [ ] **Step 3: Implement** the pages, tabs and charts against `AthleteProfile`, `AthleteCompetition` and `FigureHistory` in `types.ts`.

- [ ] **Step 4: Run and verify** — `npx vitest run` — Expected: PASS. Open `/athletes`, pick an athlete, check all three tabs against the Athletes frames.

- [ ] **Step 5: Commit**

```bash
git add web
git commit -m "feat(web): build athletes list and profile from design"
```

---

### Task 11: Clubs page (React)

**Files:**
- Create: `web/src/pages/Clubs/ClubsPage.tsx`, `ClubDetailPage.tsx`, `ClubsPage.module.css`
- Create: `web/src/charts/ClubAverageLine.tsx`
- Modify: `web/src/App.tsx`

**Interfaces:**
- `ClubsPage`: list from `GET /api/clubs`; click → `/clubs/:id`.
- `ClubDetailPage`: name heading, medals (places 1 to 3 with counts), roster table (`name`, `year_of_birth`, `country`), `ClubAverageLine` of `avg_scores` by `date`.

- [ ] **Step 1: Write the failing test** — `ClubDetailPage` with mocked data renders the roster rows and a medal count of `2` for place 2.

- [ ] **Step 2: Run to verify it fails** — `npx vitest run src/pages/Clubs` — Expected: FAIL.

- [ ] **Step 3: Implement** both pages and the chart.

- [ ] **Step 4: Run to verify it passes** — `npx vitest run` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web
git commit -m "feat(web): add clubs pages"
```

---

### Task 12: Import preview and import endpoints

**Files:**
- Modify: `api/schemas.py`
- Create: `api/routers/imports.py`; modify `api/main.py`
- Create: `tests/api/test_imports.py`

**Interfaces:**
- `POST /api/imports/preview` (multipart field `file`) → `ImportPreview`: `sha256`, `filename`, `format_id` (detected or `null`), `available_formats` (list of `PARSERS` ids), `level` (or `null`), `competition` (name), `athlete_count`, `errors` (list of strings), `warnings` (list of strings). Stores the bytes in `AQUABELY_INBOX` at the path from `upload_path(inbox, data)`.
- `POST /api/imports` JSON body `{ "sha256": str, "filename": str, "format_id": str }` → `ImportResult`: `athlete_count`, `level`. Parses the stored file, validates, calls `import_competition`. Responses: `201` on success, `409` when already imported (`DuplicateImportError`), `422` with `errors` when validation fails (`ValidationFailed`).
- Size cap: requests with a body over 50 MB are rejected with `413` and `{"detail": "File exceeds 50 MB"}` before the file is written.

- [ ] **Step 1: Write the failing tests**

```python
def test_preview_detects_format_for_a_sample_pdf(client, sample_pdf_bytes):
    r = client.post("/api/imports/preview", files={"file": ("u12.pdf", sample_pdf_bytes, "application/pdf")})
    assert r.status_code == 200 and r.json()["format_id"] == "u12"

def test_preview_rejects_oversize_upload(client):
    big = b"0" * (50 * 1024 * 1024 + 1)
    r = client.post("/api/imports/preview", files={"file": ("big.pdf", big, "application/pdf")})
    assert r.status_code == 413

def test_import_twice_returns_409(client, sample_pdf_bytes):
    files = {"file": ("u12.pdf", sample_pdf_bytes, "application/pdf")}
    preview = client.post("/api/imports/preview", files=files).json()
    body = {"sha256": preview["sha256"], "filename": preview["filename"], "format_id": preview["format_id"]}
    assert client.post("/api/imports", json=body).status_code == 201
    assert client.post("/api/imports", json=body).status_code == 409
```

`sample_pdf_bytes` reads the PDF already in `data/` used by the existing importer tests; if none is available in CI, use a fixture PDF from `tests/fixtures/`.

- [ ] **Step 2: Run to verify they fail** — `pytest tests/api/test_imports.py -v` — Expected: FAIL, `404`.

- [ ] **Step 3: Implement** the two endpoints. Read the upload in chunks and stop at 50 MB. Reuse `detect_format`, `get_parser`, `validate`, `upload_path`, `write_if_changed` and `import_competition`, exactly as `views/1_import.py` does.

- [ ] **Step 4: Run to verify they pass** — `pytest tests/api -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add api tests/api
git commit -m "feat(api): add import preview and import endpoints with 50 MB cap"
```

---

### Task 13: Import page (React)

**Files:**
- Create: `web/src/pages/Import/ImportPage.tsx`, `ImportPage.module.css`
- Modify: `web/src/App.tsx`

**Interfaces:**
- Uses `apiPostForm("/api/imports/preview", form)` and `apiPost("/api/imports", body)`. Add `apiPost<T>(path, body)` to `client.ts` in this task, with a test.
- Shows per file: name, detected format with a dropdown of `available_formats` when undetected (Import disabled until a format is chosen), level, athlete count, errors (Import disabled), warnings in a collapsible list, and the outcome message: "Imported N athletes (L3).", "Already imported.", or the error text.

- [ ] **Step 1: Write the failing test** — with a mocked preview containing `errors: ["x"]`, the Import button is disabled; with `format_id: null` the format dropdown is shown and Import is disabled until a value is chosen.

- [ ] **Step 2: Run to verify it fails** — `npx vitest run src/pages/Import` — Expected: FAIL.

- [ ] **Step 3: Implement** the page.

- [ ] **Step 4: Run to verify it passes** — `npx vitest run` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web
git commit -m "feat(web): add import page"
```

---

### Task 14: End-to-end smoke tests and visual check

**Files:**
- Create: `web/playwright.config.ts`, `web/e2e/smoke.spec.ts`
- Create: `scripts/seed_e2e.py` (creates a temporary database with the seeded fixture and prints its path)

**Interfaces:**
- `smoke.spec.ts` visits every route from the parity checklist against the seeded database, asserts the key element named in the checklist (for example the Competitions results table after selecting a competition), and asserts no console errors.
- Visual check: screenshots at 1280px and 390px saved to `web/e2e/screenshots/` for manual comparison with the Claude Design frames.

- [ ] **Step 1: Write the failing e2e test** — one test per route, checking the element the parity checklist names.

- [ ] **Step 2: Run to verify it fails** — `npx playwright test` — Expected: FAIL until the pages from Tasks 8 to 13 exist.

- [ ] **Step 3: Implement** `seed_e2e.py` and the Playwright config (`webServer` runs `uvicorn` and `vite preview` against the seeded database).

- [ ] **Step 4: Run to verify it passes** — `npx playwright test` — Expected: PASS. At 390px, no page scrolls horizontally except inside tables.

- [ ] **Step 5: Commit**

```bash
git add web scripts
git commit -m "test(web): add end-to-end smoke tests and seeded database"
```

---

### Task 15: Cutover — remove Streamlit, update deployment

**Files:**
- Delete: `app.py`, `views/`, `ui/`, `tests/test_pages_smoke.py`, Streamlit-only tests in `tests/test_components.py`
- Modify: `requirements.txt` (remove `streamlit`, `plotly`)
- Modify: `Dockerfile` (two stages: Node 20 builds `web/dist`; Python 3.12 runs `uvicorn api.main:app --host 0.0.0.0 --port 8000`)
- Modify: `docker-compose.yml` (internal port only)
- Modify: `Caddyfile` (`reverse_proxy app:8000`)
- Modify: `docs/deployment.md`
- Modify: `api/main.py` (redirects for the five old Streamlit paths, `301` to the new routes)
- Create: `tests/api/test_redirects.py`

**Interfaces:**
- Redirects: `/Import` → `/import`, `/Competitions` → `/competitions`, `/Athletes` → `/athletes`, `/Clubs` → `/clubs`, `/Figures` → `/figures`, all `301`.

- [ ] **Step 1: Write the failing test**

```python
def test_old_streamlit_paths_redirect(client):
    for old, new in [("/Import", "/import"), ("/Competitions", "/competitions"),
                     ("/Athletes", "/athletes"), ("/Clubs", "/clubs"), ("/Figures", "/figures")]:
        r = client.get(old, follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"] == new
```

- [ ] **Step 2: Run to verify it fails** — `pytest tests/api/test_redirects.py -v` — Expected: FAIL, `200`.

- [ ] **Step 3: Implement** the redirects and the deployment changes. Then remove the Streamlit files.

- [ ] **Step 4: Run the full suite and build the image**

Run: `pytest -q` — Expected: PASS. Run: `cd web && npm test && npm run build` — Expected: PASS. Run: `docker compose build app` — Expected: image builds. Run: `docker compose up -d` and `curl -u <user> https://<domain>/api/health` — Expected: `{"status":"ok"}`.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: cut over to FastAPI and React; remove Streamlit"
```

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-11-23-fastapi-react-refactor.md`. Please review the plan.

The plan has 15 tasks across two stacks. Tasks depend on each other's API contracts (backend routes define what the React pages consume), so a wrong response shape would be expensive to find late.

**Recommended: Subagent-driven.** Fresh reviewers per task catch contract mismatches between backend and frontend before the next task builds on them, and the cost of a shipped wrong number on the results or ranking pages is high.

Does the plan capture what you want, and which approach should we use?
