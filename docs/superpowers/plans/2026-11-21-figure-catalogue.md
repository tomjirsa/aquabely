# Figure Catalogue, Judge Marks and Figures Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the official figure catalogue the identity, coefficient and description source for every figure; show judge marks and coefficients in the Competitions and Athletes views; add a Figures page.

**Architecture:** A seeded `figure_catalogue` table, a matching module that maps each sheet figure (by printed code, then by alias) to a catalogue row or raises, and parsers that return the printed code with each figure. Validation and the importer use the matched coefficient. Queries and pages read the catalogue link.

**Tech Stack:** Python 3.12, SQLite, pandas, Streamlit (>=1.51), Plotly, pytest.

**Spec:** `docs/superpowers/specs/2026-11-21-figure-catalogue-design.md`

## Global Constraints

- Catalogue scope: L3 and U12 only (see spec, Catalogue table). Youth, Juniors, Seniors, Masters, Beginners L1 and L2 are not seeded.
- A U12 "Straight Ballet Leg" (code 106) and an L3 "Ballet Leg Single" (code 101) are different figures.
- Sheet figure name → catalogue: code match first (U12 sheets print a code), alias second, otherwise a validation error.
- Confirmed aliases: "Ballet Leg Single" and "Straight Ballet Leg" (L3 sheets) → code 101. "Kipnus" → 316. "Walkover Front Variant" and the Back Layout to Surface Arch name variants → the L3 entry with no code.
- Score check: trimmed mean of judge marks × catalogue coefficient, tolerance 0.05, a warning not an error (unchanged rule).
- Seeding is idempotent (`INSERT OR IGNORE`).
- Every commit message ends with `Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>`.

## Review Focus

1. A figure that matches no catalogue entry rejects the whole import and writes nothing. Test in Task 4 and Task 6.
2. U12 "Straight Ballet Leg" (106) and L3 "Ballet Leg Single" (101) stay separate figures in the rankings and the figure table. Test in Task 2 and Task 7.
3. U12 figures are score-checked with their catalogue coefficient, so a U12 score mismatch produces a warning. Test in Task 4.
4. When a sheet prints a code, the code decides the match even if the printed name differs. Test in Task 2.
5. Re-running the seed or re-importing a file does not duplicate catalogue rows or figures. Test in Task 1 and Task 6.

---

### Task 1: Catalogue table and seed data

**Files:**
- Create: `parser/catalogue.py`
- Modify: `db/schema.sql` (add the `figure_catalogue` table and its seed rows)
- Test: `tests/test_catalogue.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `CATALOGUE: list[CatalogueEntry]` in `parser/catalogue.py`, where `CatalogueEntry` is a frozen dataclass `(code: str | None, level: str, name: str, coefficient: float, description_cs: str)`. The table `figure_catalogue(id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, level TEXT NOT NULL, name TEXT NOT NULL, coefficient REAL NOT NULL, description_cs TEXT NOT NULL DEFAULT '', source TEXT NOT NULL, UNIQUE(level, code, name))`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_catalogue.py
import sqlite3
from db.database import init_schema
from parser.catalogue import CATALOGUE


def test_catalogue_has_l3_and_u12_entries():
    levels = {e.level for e in CATALOGUE}
    assert levels == {"L3", "U12"}
    l3 = {e.code: e.coefficient for e in CATALOGUE if e.level == "L3" and e.code}
    assert l3 == {"101": 1.6, "316": 1.4}
    u12 = {e.code: e.coefficient for e in CATALOGUE if e.level == "U12"}
    assert u12["106"] == 1.6 and u12["301"] == 1.8 and u12["359"] == 2.2 and u12["348"] == 1.9


def test_seed_is_idempotent():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    init_schema(conn)
    assert conn.execute("SELECT COUNT(*) FROM figure_catalogue").fetchone()[0] == len(CATALOGUE)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_catalogue.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'parser.catalogue'`

- [ ] **Step 3: Implement `CatalogueEntry` and `CATALOGUE` in `parser/catalogue.py`, and add the table and seed rows to `db/schema.sql`**

Entries are the rows in the spec's Catalogue table, plus the U12 draw-group figures "Water Drop" (363, 1.8), "Swordfish" (401, 2.1), "Kip" (311, 1.6), "Swanita Spinning 180°" (227d, 1.9). Use the spec's Czech descriptions from section 13 of `C:\Users\Tom\Downloads\SY_STD_2026.pdf` for `description_cs` where they exist; leave `''` where the document has none. Seed rows with `INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES (...)`, `source = 'SY_STD_2026'`. Entries with no code use `NULL`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_catalogue.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add parser/catalogue.py db/schema.sql tests/test_catalogue.py
git commit -m "feat: add figure catalogue table and seed data

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Matching sheet figures to the catalogue

**Files:**
- Create: `parser/figure_match.py`
- Test: `tests/test_figure_match.py`

**Interfaces:**
- Consumes: `CATALOGUE`, `CatalogueEntry` (Task 1).
- Produces:
  - `class UnmatchedFigureError(ValueError)` with attribute `figure_name: str`.
  - `ALIASES: dict[tuple[str, str], str]` mapping `(level, normalised sheet name lowercased)` to a catalogue code, or to the sentinel `"no-code:<name>"` for the codeless L3 entries. Keys are the exact normalised names the parsers produce (check them with a script over the three samples before writing the table; the spec's alias list is the source).
  - `match_figure(level: str, sheet_name: str, code: str | None) -> CatalogueEntry` — code match first (`code` and `level` against `CATALOGUE`), then the alias table, otherwise raises `UnmatchedFigureError`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_figure_match.py
import pytest
from parser.figure_match import match_figure, UnmatchedFigureError


def test_code_wins_over_printed_name():
    e = match_figure("U12", "Something Else Entirely", "106")
    assert (e.code, e.name) == ("106", "Straight Ballet Leg")


def test_l3_ballet_leg_names_both_match_101():
    assert match_figure("L3", "Ballet Leg Single", None).code == "101"
    assert match_figure("L3", "Straight Ballet Leg", None).code == "101"


def test_u12_straight_ballet_leg_is_not_l3_101():
    assert match_figure("U12", "Straight Ballet Leg", "106").code == "106"


def test_unknown_figure_raises_with_name():
    with pytest.raises(UnmatchedFigureError) as exc:
        match_figure("L3", "Mystery Spin", None)
    assert exc.value.figure_name == "Mystery Spin"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_figure_match.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'parser.figure_match'`

- [ ] **Step 3: Implement `figure_match.py`**

Build `ALIASES` from the names the three samples produce (run `L3Parser().parse` and `U12Parser().parse` once and print the distinct figure names; the spec lists the intended mappings). `match_figure` checks the code table first, then `ALIASES`, then raises. Match the catalogue on `level` as well as code.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_figure_match.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add parser/figure_match.py tests/test_figure_match.py
git commit -m "feat: match sheet figures to the catalogue by code, then alias

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Parsers return the printed code

**Files:**
- Modify: `parser/models.py` (add `code: str | None = None` as the last field of `FigureDef`)
- Modify: `parser/formats/l3.py` (`FigureDef` construction near line 165; remove the merge of "Straight Ballet Leg" into "Ballet Leg Single" from `_FIGURE_NAME_ALIASES`; keep only whitespace and title normalisation in `normalize_figure_name`)
- Modify: `parser/formats/u12.py` (`FigureDef` construction near line 112: set `code` to the printed figure ID, and `difficulty=None`)
- Test: `tests/test_l3_format.py`, `tests/test_u12_format.py`

**Interfaces:**
- Consumes: `FigureDef` (Task 1 models).
- Produces: `FigureDef(number: str, name: str, difficulty: float | None, code: str | None = None)`. L3 figures have `code=None`; U12 figures have `code` set to the printed ID (`"106"`, `"301"`, `"359"`, `"348"`).

- [ ] **Step 1: Write the failing tests**

```python
# in tests/test_u12_format.py (add)
def test_u12_figures_carry_printed_codes():
    comp = U12Parser().parse(SAMPLE)
    assert [f.code for f in comp.figures] == ["106", "301", "359", "348"]
    assert [f.name for f in comp.figures][0] == "Straight Ballet Leg"


# in tests/test_l3_format.py (add, using the BEGINNER constant)
def test_l3_figures_have_no_printed_code_and_keep_sheet_names():
    comp = L3Parser().parse(BEGINNER)
    assert all(f.code is None for f in comp.figures)
    assert comp.figures[0].name == "Straight Ballet Leg"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_u12_format.py tests/test_l3_format.py -v -k "code or sheet_names"`
Expected: FAIL (`code` attribute missing; L3 name is currently "Ballet Leg Single")

- [ ] **Step 3: Implement the model field and the parser changes**

Add the default field to `FigureDef`. In `l3.py`, delete the "Straight Ballet Leg" → "Ballet Leg Single" entry from `_FIGURE_NAME_ALIASES`. In `u12.py`, pass the captured ID as `code`. Existing tests that expected "Ballet Leg Single" for U12 F1 must be updated to "Straight Ballet Leg".

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_u12_format.py tests/test_l3_format.py tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add parser/models.py parser/formats/l3.py parser/formats/u12.py tests/test_u12_format.py tests/test_l3_format.py
git commit -m "fix: keep printed figure codes and stop merging the two Ballet Leg names

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Validation uses the catalogue

**Files:**
- Modify: `parser/validate.py` (the figure-difficulty lookup and the new unmatched-figure check)
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `match_figure`, `UnmatchedFigureError` (Task 2); `FigureDef.code` (Task 3).
- Produces: `validate(comp)` unchanged in signature. For each figure, the matched catalogue coefficient is used as `difficulty` for the score check. An unmatched figure adds an error `"unknown figure: <name>"` and no score check for it.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_validate.py (add)
def test_unmatched_figure_is_an_error():
    comp = _comp_with_figure(name="Mystery Spin", code=None, level="L3")
    rep = validate(comp)
    assert any("unknown figure: Mystery Spin" in e for e in rep.errors)


def test_u12_score_is_checked_with_catalogue_coefficient():
    # Straight Ballet Leg 106 has coefficient 1.6; a mean of 5.0 gives 8.0
    comp = _comp_with_figure(name="Straight Ballet Leg", code="106", level="U12", marks=[5.0] * 5, score=8.0)
    assert validate(comp).warnings == []
    comp_bad = _comp_with_figure(name="Straight Ballet Leg", code="106", level="U12", marks=[5.0] * 5, score=5.0)
    assert any("Straight Ballet Leg" in w for w in validate(comp_bad).warnings)
```

`_comp_with_figure` is a helper added to the same test file that builds a one-athlete `ParsedCompetition` with the given figure, level, code, judge marks and score. It must use `judges_per_figure=5` for the U12 case.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_validate.py -v -k "unmatched or catalogue"`
Expected: FAIL (no unknown-figure error yet; U12 score not checked)

- [ ] **Step 3: Implement the change in `validate.py`**

For each `FigureDef`, call `match_figure(comp.level_code, f.name, f.code)`. On `UnmatchedFigureError`, append the error and skip that figure's score check. Otherwise use `entry.coefficient` as the difficulty for the score check (keep the trimmed-mean rule and the 0.05 tolerance).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_validate.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add parser/validate.py tests/test_validate.py
git commit -m "feat: validate figures against the catalogue and check U12 scores

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Schema link from figures to the catalogue

**Files:**
- Modify: `db/schema.sql` (`figures` gains `catalogue_id INTEGER REFERENCES figure_catalogue(id)`)
- Test: `tests/test_schema.py`

**Interfaces:**
- Consumes: `figure_catalogue` (Task 1).
- Produces: `figures(id, competition_category_id, number, name, difficulty, catalogue_id)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_schema.py (add)
def test_figures_link_to_catalogue(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(figures)")}
    assert "catalogue_id" in cols
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_schema.py -v -k catalogue`
Expected: FAIL (`catalogue_id` not in columns)

- [ ] **Step 3: Add the column to the `figures` definition**

Add `catalogue_id INTEGER REFERENCES figure_catalogue(id)` after `difficulty`. Because the schema is fresh and the table is created with `IF NOT EXISTS`, the test database must be created from the new schema (use an in-memory DB in the test).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add db/schema.sql tests/test_schema.py
git commit -m "feat: link figures to the catalogue

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Importer writes the catalogue link and coefficient

**Files:**
- Modify: `db/importer.py` (the figures insert near line 65)
- Test: `tests/test_importer.py`

**Interfaces:**
- Consumes: `match_figure` (Task 2), `FigureDef.code` (Task 3), `figure_catalogue` rows, `validate` (Task 4).
- Produces: `import_competition` unchanged in signature. Each `figures` row stores `catalogue_id` and `difficulty` = catalogue coefficient. A figure that cannot be matched raises `ValidationFailed` before any write, and the rejected `imports` row is logged, as the existing validation path does.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_importer.py (add)
def test_import_links_figures_to_catalogue_and_stores_coefficient(conn):
    comp = _u12_comp_with_figure(code="106", name="Straight Ballet Leg")
    import_competition(conn, comp, sha256="cat1", filename="u12.pdf")
    row = conn.execute("SELECT f.difficulty, c.code FROM figures f JOIN figure_catalogue c ON c.id = f.catalogue_id").fetchone()
    assert row == (1.6, "106")


def test_unmatched_figure_rejects_import_and_writes_nothing(conn):
    comp = _l3_comp_with_figure(name="Mystery Spin")
    with pytest.raises(ValidationFailed):
        import_competition(conn, comp, sha256="cat2", filename="bad.pdf")
    assert conn.execute("SELECT COUNT(*) FROM figures").fetchone()[0] == 0
    assert conn.execute("SELECT status FROM imports").fetchone()[0] == "rejected"
```

The helpers `_u12_comp_with_figure` and `_l3_comp_with_figure` are added to the test file and build a one-athlete `ParsedCompetition`. The `conn` fixture already seeds the categories.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_importer.py -v -k "catalogue or unmatched"`
Expected: FAIL (figures not linked)

- [ ] **Step 3: Implement the change in `importer.py`**

Before the transaction, match every figure with `match_figure` (on `UnmatchedFigureError`, reject through the existing `_log` path). Inside the transaction, insert `catalogue_id` and set `difficulty` from the matched coefficient. Look up the catalogue id by `(level, code, name)`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_importer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add db/importer.py tests/test_importer.py
git commit -m "feat: store catalogue link and coefficient on import

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Queries for judge marks, coefficients and the Figures page

**Files:**
- Modify: `db/queries.py` (add `competition_figure_detail`, `athlete_figure_detail`, `catalogue_figures`)
- Test: `tests/test_queries.py`

**Interfaces:**
- Consumes: schema (Tasks 2–6).
- Produces (all return `pandas.DataFrame`):
  - `competition_figure_detail(conn, competition_category_id: int) -> DataFrame` with columns `athlete, rank, figure_name, coefficient, judge_1 ... judge_7, figure_score, figure_penalty`, one row per (result, figure), with the catalogue name and coefficient. Judge columns that are NULL stay NULL.
  - `athlete_figure_detail(conn, athlete_id: int) -> DataFrame` with columns `competition, date, figure_name, coefficient, judge_1 ... judge_7, figure_score`.
  - `catalogue_figures(conn, level: str) -> DataFrame` with columns `code, name, coefficient, description_cs, performances, competitions` where `competitions` is a comma-separated list of competition names, ordered by date.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_queries.py (add)
def test_competition_figure_detail_has_name_and_coefficient(seeded_u12):
    df = competition_figure_detail(seeded_u12.conn, seeded_u12.cc_id)
    row = df.iloc[0]
    assert row["figure_name"] == "Straight Ballet Leg"
    assert row["coefficient"] == 1.6
    assert row["judge_1"] == 5.0 and pd.isna(row["judge_6"])


def test_catalogue_figures_counts_performances_and_competitions(seeded_u12):
    df = catalogue_figures(seeded_u12.conn, "U12")
    row = df[df["code"] == "106"].iloc[0]
    assert row["performances"] == 1
    assert row["competitions"] == seeded_u12.competition_name
```

`seeded_u12` is a fixture added to the test module: a fresh in-memory DB, one U12 competition with one athlete and one figure (code 106) with judge marks `[5.0]*5`, built through `import_competition`. It exposes `conn`, `cc_id` and `competition_name`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_queries.py -v -k "figure_detail or catalogue_figures"`
Expected: FAIL with `ImportError` for the new functions

- [ ] **Step 3: Implement the three query functions**

Use parameterised SQL. Join `figures` → `figure_catalogue` for name, coefficient and code. For `catalogue_figures`, a `LEFT JOIN` from the catalogue to `figures` and `results`, `GROUP_CONCAT(DISTINCT c.name)` ordered by date for `competitions`, and `COUNT(fr.id)` for `performances`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_queries.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add db/queries.py tests/test_queries.py
git commit -m "feat: add figure detail and catalogue queries

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Competitions and Athletes views show judge marks and coefficients

**Files:**
- Modify: `views/2_competitions.py` (add a figure detail expander per competition)
- Modify: `views/3_athletes.py` (add a figure detail section under "Figure ranks")
- Test: `tests/test_pages_smoke.py`

**Interfaces:**
- Consumes: `competition_figure_detail`, `athlete_figure_detail` (Task 7); `inject_theme` (Task 10 of the earlier plan).

- [ ] **Step 1: Write the failing smoke test**

```python
# tests/test_pages_smoke.py (add)
def test_athletes_page_renders_figure_detail_with_seeded_data(seeded_app_db):
    at = AppTest.from_file("views/3_athletes.py", default_timeout=30).run()
    assert not at.exception
    assert any("Figure detail" in h.value for h in at.subheader)
```

`seeded_app_db` is a fixture that points `AQUABELY_DB` at a temp file seeded with one U12 competition (same builder as Task 7).

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pages_smoke.py -v -k figure_detail`
Expected: FAIL (no "Figure detail" subheader yet)

- [ ] **Step 3: Implement the sections**

On the Athletes page, add `st.subheader("Figure detail")` after the figure ranks, showing `athlete_figure_detail` as a table with the coefficient and judge columns (dropping all-NULL judge columns, as the Competitions page already does). On the Competitions page, add an expander per result with `competition_figure_detail` for that competition. Figure columns use the catalogue name only.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pages_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add views/2_competitions.py views/3_athletes.py tests/test_pages_smoke.py
git commit -m "feat: show judge marks and coefficients on competitions and athletes pages

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Figures page

**Files:**
- Create: `views/5_figures.py`
- Modify: `app.py` (register the page between Competitions and Athletes)
- Test: `tests/test_pages_smoke.py`

**Interfaces:**
- Consumes: `catalogue_figures` (Task 7), `inject_theme` (earlier UI task).

Behaviour: a level selector (L3 / U12) using `st.radio`, a table of `catalogue_figures` for that level with columns `code, name, coefficient, description_cs, performances, competitions`, and an empty-state message when there are no performances or entries. Calls `inject_theme()` first.

- [ ] **Step 1: Write the failing smoke test**

```python
# tests/test_pages_smoke.py (add)
def test_figures_page_renders_on_empty_database(tmp_path, monkeypatch):
    monkeypatch.setenv("AQUABELY_DB", str(tmp_path / "f.db"))
    at = AppTest.from_file("views/5_figures.py", default_timeout=20).run()
    assert not at.exception
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pages_smoke.py -v -k figures_page`
Expected: FAIL with `FileNotFoundError` for `views/5_figures.py`

- [ ] **Step 3: Implement the page and register it**

Create `views/5_figures.py` as described. In `app.py`, add `st.Page("views/5_figures.py", title="Figures", icon="🩰")` between Competitions and Athletes.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pages_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add views/5_figures.py app.py tests/test_pages_smoke.py
git commit -m "feat: add figures page with catalogue, coefficients and descriptions

Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>"
```

---

### Task 10: End-to-end check on the sample PDFs

**Files:** none changed. Verification only, against a scratch database under the session scratchpad (never the user's default database).

- [ ] **Step 1: Run the full suite**

Run: `python -m pytest -q` with `AQUABELY_DB` set to a scratch file. Expected: all tests pass.

- [ ] **Step 2: Import the three samples into a fresh scratch database**

Use `detect_format`, `parse`, `validate` and `import_competition` (with `hashlib.sha256` of the bytes), as in the earlier end-to-end script. Expected: zero errors on all three; the U12 figure codes are 106, 301, 359, 348; the L3 Beginner and Hersalkova F1 both link to catalogue code 101.

- [ ] **Step 3: Browser check**

Start the app on the scratch database. Check the Athletes page for Jirsíková Gabriela (figure detail with judge marks and coefficients), the Competitions page expander, and the Figures page for U12 (code 106 with its performance). Expected: no exceptions; screenshots reviewed.

- [ ] **Step 4: Report**

Record the test count, the three-sample results, and the screenshot paths. No commit in this task.

---

## Self-Review

- **Spec coverage:** catalogue (Task 1), matching with code and alias (Task 2), printed codes and the Ballet Leg split (Task 3), validation with coefficients and unmatched errors (Task 4), figures link (Task 5), importer (Task 6), queries (Task 7), overview views (Task 8), Figures page (Task 9), end-to-end (Task 10). Spec's "Figures page filter" question is answered by Task 9 showing all catalogue entries for the level, with performance counts (the spec asked whether to show only performed figures; this plan shows all, pending the user's answer).
- **Types:** `CatalogueEntry`, `UnmatchedFigureError`, `match_figure`, `FigureDef.code` and the three query functions are named identically wherever they are used.
- **Open point:** the exact normalised sheet names for the L3 alias keys must be read from the samples in Task 2 Step 3; the plan says so rather than guessing them.
