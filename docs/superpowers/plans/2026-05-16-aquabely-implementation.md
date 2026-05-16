# Aquabely Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Streamlit app that parses artistic swimming competition PDFs into SQLite and provides athlete/club/competition dashboards.

**Architecture:** PDF files land in `~/aquabely_inbox`; an Import page parses them with pdfplumber and writes structured data to `~/aquabely.db` (SQLite). Three dashboard pages (Athlete, Club, Competition) query the DB directly with pandas + plotly.

**Tech Stack:** Python 3.11+, streamlit, pdfplumber, pandas, plotly, sqlite3 (stdlib), pytest

---

## File Map

```
aquabely/
  app.py                        # st.navigation entry point
  pages/
    1_import.py                 # list inbox PDFs, import button
    2_athlete.py                # athlete search + score timeline
    3_club.py                   # club roster + medal tally
    4_competition.py            # competition → category → results table
  db/
    __init__.py
    schema.sql                  # DDL for all six tables
    database.py                 # get_connection(), init_schema(), queries
  parser/
    __init__.py
    pdf_parser.py               # pdfplumber → ParsedPDF dataclasses
  tests/
    test_pdf_parser.py
    test_database.py
  requirements.txt
```

---

### Task 1: Project scaffold

**Files:**
- Create: `requirements.txt`
- Create: `app.py`
- Create: `db/__init__.py`, `parser/__init__.py`
- Create: `pages/` directory

- [ ] **Step 1: Create requirements.txt**

```
streamlit>=1.35
pdfplumber>=0.11
plotly>=5.20
pandas>=2.2
pytest>=8.0
```

- [ ] **Step 2: Create empty package init files**

```bash
mkdir -p pages db parser tests
touch db/__init__.py parser/__init__.py tests/__init__.py
```

- [ ] **Step 3: Create app.py**

```python
import streamlit as st

pg = st.navigation([
    st.Page("pages/1_import.py", title="Import", icon="📥"),
    st.Page("pages/2_athlete.py", title="Athletes", icon="🏊"),
    st.Page("pages/3_club.py", title="Clubs", icon="🏆"),
    st.Page("pages/4_competition.py", title="Competitions", icon="📋"),
])
pg.run()
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 5: Verify app starts**

```bash
streamlit run app.py
```

Expected: browser opens with four nav items, each page shows an empty body.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt app.py db/__init__.py parser/__init__.py tests/__init__.py
git commit -m "feat: project scaffold"
```

---

### Task 2: Database schema and helpers

**Files:**
- Create: `db/schema.sql`
- Create: `db/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_database.py`:

```python
import sqlite3
import pytest
from pathlib import Path
import db.database as database


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")


def test_init_schema_creates_tables():
    database.init_schema()
    with database.get_connection() as conn:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    assert tables == {
        "competitions", "categories", "figures",
        "athletes", "results", "figure_results", "imported_files"
    }


def test_is_imported_returns_false_for_unknown():
    database.init_schema()
    assert database.is_imported("abc123") is False


def test_is_imported_returns_true_after_insert(sample_parsed_pdf):
    database.init_schema()
    database.insert_pdf_result(sample_parsed_pdf, "test.pdf", "abc123")
    assert database.is_imported("abc123") is True


def test_insert_stores_athlete(sample_parsed_pdf):
    database.init_schema()
    database.insert_pdf_result(sample_parsed_pdf, "test.pdf", "deadbeef")
    with database.get_connection() as conn:
        row = conn.execute("SELECT name, club FROM athletes LIMIT 1").fetchone()
    assert row["name"] == "Test Athlete"
    assert row["club"] == "Test Club"


def test_insert_stores_result(sample_parsed_pdf):
    database.init_schema()
    database.insert_pdf_result(sample_parsed_pdf, "test.pdf", "deadbeef2")
    with database.get_connection() as conn:
        row = conn.execute("SELECT rank, total_score FROM results LIMIT 1").fetchone()
    assert row["rank"] == 1
    assert abs(row["total_score"] - 60.56) < 0.01


def test_insert_idempotent(sample_parsed_pdf):
    database.init_schema()
    database.insert_pdf_result(sample_parsed_pdf, "test.pdf", "sha1")
    # second insert with same sha should not raise
    database.insert_pdf_result(sample_parsed_pdf, "test2.pdf", "sha1")
    with database.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    assert count == 1  # only one insert happened
```

Add the fixture to `tests/conftest.py` (create it):

```python
import pytest
from parser.pdf_parser import ParsedPDF, FigureDef, FigureResult, AthleteResult


@pytest.fixture
def sample_parsed_pdf():
    return ParsedPDF(
        competition_name="Test Cup",
        date="01.01.2026",
        category_name="Beginner L1",
        figures=[
            FigureDef("F1", "Ballet Leg", 1.6),
            FigureDef("F2", "Kipnus", 1.4),
        ],
        results=[
            AthleteResult(
                rank=1,
                entry_number=5,
                name="Test Athlete",
                club="Test Club",
                country="CZE",
                yob=2015,
                total_score=60.56,
                penalty=0.0,
                points_behind=0.0,
                figure_results=[
                    FigureResult("F1", [6.0, 6.1, 6.2, 6.0, 6.1, 6.0, 6.0], 9.44, 0.0),
                    FigureResult("F2", [5.8, 5.9, 6.0, 5.8, 5.9, 5.8, 5.8], 8.32, 0.0),
                ],
            )
        ],
    )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_database.py -v
```

Expected: ImportError or AttributeError — `database` module doesn't exist yet.

- [ ] **Step 3: Create db/schema.sql**

```sql
CREATE TABLE IF NOT EXISTS competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    location TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL REFERENCES competitions(id),
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS figures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    number TEXT NOT NULL,
    name TEXT NOT NULL,
    difficulty REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    club TEXT NOT NULL,
    year_of_birth INTEGER,
    UNIQUE(name, club)
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_id INTEGER NOT NULL REFERENCES athletes(id),
    category_id INTEGER NOT NULL REFERENCES categories(id),
    entry_number INTEGER,
    rank INTEGER NOT NULL,
    total_score REAL NOT NULL,
    penalty REAL NOT NULL DEFAULT 0.0,
    points_behind REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS figure_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL REFERENCES results(id),
    figure_id INTEGER NOT NULL REFERENCES figures(id),
    score REAL NOT NULL,
    penalty REAL NOT NULL DEFAULT 0.0,
    judge_1 REAL, judge_2 REAL, judge_3 REAL, judge_4 REAL,
    judge_5 REAL, judge_6 REAL, judge_7 REAL
);

CREATE TABLE IF NOT EXISTS imported_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    UNIQUE(sha256)
);
```

- [ ] **Step 4: Create db/database.py**

```python
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "aquabely.db"
_SCHEMA = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema():
    with get_connection() as conn:
        conn.executescript(_SCHEMA.read_text())


def is_imported(sha256: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM imported_files WHERE sha256 = ?", (sha256,)
        ).fetchone()
    return row is not None


def insert_pdf_result(parsed, filename: str, sha256: str):
    if is_imported(sha256):
        return
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO competitions (name, date) VALUES (?, ?)",
            (parsed.competition_name, parsed.date),
        )
        competition_id = cur.lastrowid

        cur = conn.execute(
            "INSERT INTO categories (competition_id, name) VALUES (?, ?)",
            (competition_id, parsed.category_name),
        )
        category_id = cur.lastrowid

        figure_ids = {}
        for fig in parsed.figures:
            cur = conn.execute(
                "INSERT INTO figures (category_id, number, name, difficulty) VALUES (?, ?, ?, ?)",
                (category_id, fig.number, fig.name, fig.difficulty),
            )
            figure_ids[fig.number] = cur.lastrowid

        for result in parsed.results:
            conn.execute(
                "INSERT OR IGNORE INTO athletes (name, country, club, year_of_birth) VALUES (?, ?, ?, ?)",
                (result.name, result.country, result.club, result.yob),
            )
            athlete_id = conn.execute(
                "SELECT id FROM athletes WHERE name = ? AND club = ?",
                (result.name, result.club),
            ).fetchone()["id"]

            cur = conn.execute(
                "INSERT INTO results (athlete_id, category_id, entry_number, rank, total_score, penalty, points_behind) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (athlete_id, category_id, result.entry_number, result.rank,
                 result.total_score, result.penalty, result.points_behind),
            )
            result_id = cur.lastrowid

            for fr in result.figure_results:
                fig_id = figure_ids.get(fr.figure_number)
                if fig_id is None:
                    continue
                judges = (fr.judge_scores + [None] * 7)[:7]
                conn.execute(
                    "INSERT INTO figure_results "
                    "(result_id, figure_id, score, penalty, judge_1, judge_2, judge_3, judge_4, judge_5, judge_6, judge_7) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (result_id, fig_id, fr.score, fr.penalty, *judges),
                )

        conn.execute(
            "INSERT INTO imported_files (filename, sha256, imported_at) VALUES (?, ?, ?)",
            (filename, sha256, datetime.now().isoformat()),
        )
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_database.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add db/ tests/test_database.py tests/conftest.py tests/__init__.py
git commit -m "feat: database schema and helpers"
```

---

### Task 3: PDF parser

**Files:**
- Create: `parser/pdf_parser.py`
- Create: `tests/test_pdf_parser.py`

The sample PDF lives at `~/Downloads/result_detail_Beginner L3 FIG (2019-2014).pdf`. Tests run against it directly.

The PDF layout: each page has a table where each athlete occupies 4 rows (one per figure). The first row of each athlete block contains rank, country, `{entry_number} - {name}\n{club}`, year of birth, figure label (F1), 7 judge scores, figure score, penalty, total score, and points-behind. Rows 2–4 contain only the figure label (F2/F3/F4), judge scores, figure score, and penalty.

- [ ] **Step 1: Write failing tests**

Create `tests/test_pdf_parser.py`:

```python
from pathlib import Path
import pytest
from parser.pdf_parser import parse_pdf, file_sha256

SAMPLE = Path.home() / "Downloads" / "result_detail_Beginner L3 FIG (2019-2014).pdf"

pytestmark = pytest.mark.skipif(not SAMPLE.exists(), reason="sample PDF not found")


def test_competition_name():
    r = parse_pdf(SAMPLE)
    assert r.competition_name == "Delfinek cup"


def test_date():
    r = parse_pdf(SAMPLE)
    assert r.date == "16.05.2026"


def test_category_name():
    r = parse_pdf(SAMPLE)
    assert "Beginner L3 FIG" in r.category_name


def test_figures_count():
    r = parse_pdf(SAMPLE)
    assert len(r.figures) == 4


def test_first_figure():
    r = parse_pdf(SAMPLE)
    f = r.figures[0]
    assert f.number == "F1"
    assert "Ballet Leg" in f.name
    assert f.difficulty == 1.6


def test_result_count():
    r = parse_pdf(SAMPLE)
    assert len(r.results) == 43


def test_first_athlete_identity():
    r = parse_pdf(SAMPLE)
    a = r.results[0]
    assert a.rank == 1
    assert a.name == "Chromíková Sára"
    assert a.club == "Delfínek Ostrava"
    assert a.country == "CZE"
    assert a.yob == 2016
    assert a.entry_number == 34


def test_first_athlete_score():
    r = parse_pdf(SAMPLE)
    assert abs(r.results[0].total_score - 60.5636) < 0.01


def test_first_athlete_figure_results():
    r = parse_pdf(SAMPLE)
    frs = r.results[0].figure_results
    assert len(frs) == 4
    assert abs(frs[0].score - 9.9440) < 0.01
    assert frs[0].figure_number == "F1"
    assert len(frs[0].judge_scores) == 7


def test_points_behind_first_place():
    r = parse_pdf(SAMPLE)
    assert r.results[0].points_behind == 0.0


def test_points_behind_second_place():
    r = parse_pdf(SAMPLE)
    assert abs(r.results[1].points_behind - 2.74) < 0.01


def test_sha256_stable():
    h1 = file_sha256(SAMPLE)
    h2 = file_sha256(SAMPLE)
    assert h1 == h2
    assert len(h1) == 64
```

- [ ] **Step 2: Run to confirm all fail**

```bash
pytest tests/test_pdf_parser.py -v
```

Expected: ImportError — module doesn't exist.

- [ ] **Step 3: Inspect raw pdfplumber output (debug step)**

Before writing the full parser, verify the actual table structure:

```python
# run this once in a python shell to see what pdfplumber gives us
import pdfplumber
from pathlib import Path

path = Path.home() / "Downloads" / "result_detail_Beginner L3 FIG (2019-2014).pdf"
with pdfplumber.open(path) as pdf:
    print("=== PAGE 1 TEXT (first 800 chars) ===")
    print(pdf.pages[0].extract_text()[:800])
    print("\n=== PAGE 1 TABLE (first 10 rows) ===")
    table = pdf.pages[0].extract_table()
    if table:
        for row in table[:10]:
            print(row)
    else:
        print("No table found — check extract_tables()")
        for t in pdf.pages[0].extract_tables():
            print("Table:", t[:3])
```

Run it:
```bash
python -c "
import pdfplumber
from pathlib import Path
path = Path.home() / 'Downloads' / 'result_detail_Beginner L3 FIG (2019-2014).pdf'
with pdfplumber.open(path) as pdf:
    print(pdf.pages[0].extract_text()[:800])
    print('---')
    t = pdf.pages[0].extract_table()
    for row in (t or [])[:8]:
        print(row)
"
```

Use the output to verify column indices (rank=0, country=1, name/club=2, YOB=3, figure=4, judges=5-11, score=12, penalty=13, total=14, points_behind=15). Adjust indices in Step 4 if they differ.

- [ ] **Step 4: Create parser/pdf_parser.py**

```python
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber


@dataclass
class FigureDef:
    number: str
    name: str
    difficulty: float


@dataclass
class FigureResult:
    figure_number: str
    judge_scores: list
    score: float
    penalty: float


@dataclass
class AthleteResult:
    rank: int
    entry_number: int
    name: str
    club: str
    country: str
    yob: int
    total_score: float
    penalty: float
    points_behind: float
    figure_results: list = field(default_factory=list)


@dataclass
class ParsedPDF:
    competition_name: str
    date: str
    category_name: str
    figures: list
    results: list


def parse_pdf(path: Path) -> ParsedPDF:
    all_text_pages = []
    all_rows = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text_pages.append(text)
            table = page.extract_table()
            if table:
                all_rows.extend(table)

    full_text = "\n".join(all_text_pages)
    comp_name, date, category = _parse_header(full_text)
    figures = _parse_figures(full_text)
    results = _parse_results(all_rows, figures)

    return ParsedPDF(comp_name, date, category, figures, results)


def _parse_header(text: str):
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    comp_name = lines[0] if lines else "Unknown"
    date, category = "", ""
    if len(lines) > 1:
        m = re.match(
            r"(\d{2}\.\d{2}\.\d{4})\s*-\s*(?:\d{2}\.\d{2}\.\d{4})?\s*-?\s*(.*)",
            lines[1],
        )
        if m:
            date = m.group(1)
            category = m.group(2).strip().strip("-").strip()
    return comp_name, date, category


def _parse_figures(text: str) -> list:
    figures = []
    for m in re.finditer(r"(F\d+):\s*(.*?)\s*\((\d+\.\d+)\)", text):
        figures.append(
            FigureDef(
                number=m.group(1),
                name=m.group(2).strip(),
                difficulty=float(m.group(3)),
            )
        )
    return figures


def _parse_results(rows: list, figures: list) -> list:
    n_figures = len(figures) or 4
    figure_numbers = [f.number for f in figures] or [f"F{i+1}" for i in range(n_figures)]

    # drop header row(s): any row where first cell is "Rank" or similar
    data_rows = []
    for row in rows:
        if not row:
            continue
        first = str(row[0] or "").strip()
        if first.lower() in ("rank", ""):
            # skip header rows and rows that are page continuations
            if first.lower() == "rank":
                continue
        data_rows.append(row)

    results = []
    i = 0
    while i < len(data_rows):
        row = data_rows[i]
        rank_val = str(row[0] or "").strip()
        if not re.match(r"^\d+\.$", rank_val):
            i += 1
            continue

        rank = int(rank_val.rstrip("."))
        country = str(row[1] or "").strip()

        name_club_raw = str(row[2] or "").strip()
        entry_number, name, club = 0, "", ""
        parts = name_club_raw.split("\n")
        m = re.match(r"(\d+)\s*-\s*(.*)", parts[0])
        if m:
            entry_number = int(m.group(1))
            name = m.group(2).strip()
        else:
            name = parts[0]
        if len(parts) > 1:
            club = parts[1].strip()

        yob_raw = str(row[3] or "").strip()
        yob = int(yob_raw) if yob_raw.isdigit() else 0

        total_score = _f(row[14] if len(row) > 14 else None)
        points_behind = _f(row[15] if len(row) > 15 else None)

        figure_results = []
        block = data_rows[i : i + n_figures]
        for j, frow in enumerate(block):
            fig_num = figure_numbers[j] if j < len(figure_numbers) else f"F{j+1}"
            judges = [_f(frow[k] if len(frow) > k else None) for k in range(5, 12)]
            score = _f(frow[12] if len(frow) > 12 else None)
            pen = _f(frow[13] if len(frow) > 13 else None)
            figure_results.append(FigureResult(fig_num, judges, score, pen))

        total_penalty = sum(fr.penalty for fr in figure_results)

        results.append(
            AthleteResult(
                rank=rank,
                entry_number=entry_number,
                name=name,
                club=club,
                country=country,
                yob=yob,
                total_score=total_score,
                penalty=total_penalty,
                points_behind=points_behind,
                figure_results=figure_results,
            )
        )
        i += n_figures

    return results


def _f(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(str(val).strip().replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_pdf_parser.py -v
```

Expected: most tests PASS. If column indices are off (values are 0.0 when they shouldn't be), revisit the debug output from Step 3 and adjust the column indices in `_parse_results` (the `row[5]..row[15]` accesses).

- [ ] **Step 6: Fix any failing assertions**

If `test_competition_name` fails: check that `lines[0]` in `_parse_header` really is "Delfinek cup" (not a page number or blank line). Add a guard: skip lines that are purely numeric or match `"© \d+"`.

If `test_first_athlete_identity` fails on `name`: the `name_club_raw` cell may use a different separator than `\n`. Add a fallback: also try splitting on `\n` replaced by a space, then use the regex.

- [ ] **Step 7: Run all tests**

```bash
pytest -v
```

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add parser/ tests/test_pdf_parser.py tests/conftest.py
git commit -m "feat: PDF parser with tests"
```

---

### Task 4: Import page

**Files:**
- Create: `pages/1_import.py`

No automated tests for Streamlit pages — verify manually.

- [ ] **Step 1: Create pages/1_import.py**

```python
from pathlib import Path

import streamlit as st

import db.database as database
from parser.pdf_parser import file_sha256, parse_pdf

INBOX = Path.home() / "aquabely_inbox"

st.title("Import Results")

database.init_schema()
INBOX.mkdir(exist_ok=True)

pdfs = sorted(INBOX.glob("*.pdf"))
if not pdfs:
    st.info(f"No PDFs found in {INBOX}. Drop result PDF files there to import them.")
    st.stop()

for pdf in pdfs:
    sha = file_sha256(pdf)
    already = database.is_imported(sha)
    col1, col2 = st.columns([4, 1])
    col1.write(f"{'✅' if already else '🔸'} `{pdf.name}`")
    if not already:
        if col2.button("Import", key=str(pdf)):
            with st.spinner(f"Parsing {pdf.name}…"):
                try:
                    parsed = parse_pdf(pdf)
                    database.insert_pdf_result(parsed, pdf.name, sha)
                    st.success(
                        f"Imported **{len(parsed.results)}** athletes — "
                        f"{parsed.competition_name} / {parsed.category_name}"
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed: {exc}")
```

- [ ] **Step 2: Manual smoke test**

```bash
mkdir -p ~/aquabely_inbox
cp ~/Downloads/"result_detail_Beginner L3 FIG (2019-2014).pdf" ~/aquabely_inbox/
streamlit run app.py
```

Navigate to Import page. Expected: file listed with 🔸. Click Import. Expected: success message "Imported 43 athletes". Reload — file now shows ✅. Click Import again — button gone.

- [ ] **Step 3: Commit**

```bash
git add pages/1_import.py
git commit -m "feat: import page"
```

---

### Task 5: Athlete dashboard

**Files:**
- Create: `pages/2_athlete.py`

- [ ] **Step 1: Create pages/2_athlete.py**

```python
import pandas as pd
import plotly.express as px
import streamlit as st

import db.database as database

st.title("Athletes")

database.init_schema()

with database.get_connection() as conn:
    athletes = pd.read_sql(
        "SELECT id, name, club, country, year_of_birth FROM athletes ORDER BY name",
        conn,
    )

if athletes.empty:
    st.info("No data yet — import PDFs on the Import page.")
    st.stop()

name = st.selectbox("Athlete", athletes["name"].tolist())
row = athletes[athletes["name"] == name].iloc[0]
st.caption(f"{row['club']} · {row['country']} · born {row['year_of_birth']}")

with database.get_connection() as conn:
    df = pd.read_sql(
        """
        SELECT c.name AS competition, c.date, cat.name AS category,
               r.rank, r.total_score, r.points_behind
        FROM results r
        JOIN athletes a ON a.id = r.athlete_id
        JOIN categories cat ON cat.id = r.category_id
        JOIN competitions c ON c.id = cat.competition_id
        WHERE a.name = ?
        ORDER BY c.date
        """,
        conn,
        params=(name,),
    )

if df.empty:
    st.info("No results found for this athlete.")
    st.stop()

st.dataframe(df, use_container_width=True)

fig = px.line(
    df, x="date", y="total_score", markers=True,
    title="Total score over time", labels={"total_score": "Score", "date": "Date"},
)
st.plotly_chart(fig, use_container_width=True)

# per-figure breakdown
with database.get_connection() as conn:
    fig_df = pd.read_sql(
        """
        SELECT c.date, c.name AS competition, f.number AS figure,
               fr.score AS figure_score
        FROM figure_results fr
        JOIN results r ON r.id = fr.result_id
        JOIN figures f ON f.id = fr.figure_id
        JOIN athletes a ON a.id = r.athlete_id
        JOIN categories cat ON cat.id = r.category_id
        JOIN competitions c ON c.id = cat.competition_id
        WHERE a.name = ?
        ORDER BY c.date, f.number
        """,
        conn,
        params=(name,),
    )

if not fig_df.empty:
    fig2 = px.bar(
        fig_df, x="competition", y="figure_score", color="figure",
        barmode="group", title="Figure scores per competition",
    )
    st.plotly_chart(fig2, use_container_width=True)
```

- [ ] **Step 2: Manual smoke test**

Run `streamlit run app.py`, navigate to Athletes. Select "Chromíková Sára". Expected: caption shows "Delfínek Ostrava · CZE · born 2016", table with one row, score timeline with one data point, bar chart with 4 figures.

- [ ] **Step 3: Commit**

```bash
git add pages/2_athlete.py
git commit -m "feat: athlete dashboard"
```

---

### Task 6: Club dashboard

**Files:**
- Create: `pages/3_club.py`

- [ ] **Step 1: Create pages/3_club.py**

```python
import pandas as pd
import plotly.express as px
import streamlit as st

import db.database as database

st.title("Clubs")

database.init_schema()

with database.get_connection() as conn:
    clubs = pd.read_sql(
        "SELECT DISTINCT club FROM athletes ORDER BY club", conn
    )

if clubs.empty:
    st.info("No data yet — import PDFs on the Import page.")
    st.stop()

club = st.selectbox("Club", clubs["club"].tolist())

with database.get_connection() as conn:
    df = pd.read_sql(
        """
        SELECT a.name, a.country, c.name AS competition, c.date,
               cat.name AS category, r.rank, r.total_score
        FROM results r
        JOIN athletes a ON a.id = r.athlete_id
        JOIN categories cat ON cat.id = r.category_id
        JOIN competitions c ON c.id = cat.competition_id
        WHERE a.club = ?
        ORDER BY c.date, r.rank
        """,
        conn,
        params=(club,),
    )

if df.empty:
    st.info("No results found for this club.")
    st.stop()

st.dataframe(df, use_container_width=True)

col1, col2 = st.columns(2)

medals = (
    df[df["rank"] <= 3]
    .groupby("rank")
    .size()
    .reset_index(name="count")
)
medals["medal"] = medals["rank"].map({1: "🥇 Gold", 2: "🥈 Silver", 3: "🥉 Bronze"})
col1.subheader("Medal tally")
col1.dataframe(medals[["medal", "count"]], use_container_width=True)

avg = df.groupby("competition")["total_score"].mean().reset_index()
fig = px.bar(
    avg, x="competition", y="total_score",
    title="Avg score per competition", labels={"total_score": "Avg score"},
)
col2.plotly_chart(fig, use_container_width=True)
```

- [ ] **Step 2: Manual smoke test**

Navigate to Clubs, select "Delfínek Ostrava". Expected: results table, medal tally (1 Gold visible from the sample PDF), bar chart.

- [ ] **Step 3: Commit**

```bash
git add pages/3_club.py
git commit -m "feat: club dashboard"
```

---

### Task 7: Competition browser

**Files:**
- Create: `pages/4_competition.py`

- [ ] **Step 1: Create pages/4_competition.py**

```python
import pandas as pd
import streamlit as st

import db.database as database

st.title("Competitions")

database.init_schema()

with database.get_connection() as conn:
    comps = pd.read_sql(
        "SELECT id, name, date FROM competitions ORDER BY date DESC", conn
    )

if comps.empty:
    st.info("No data yet — import PDFs on the Import page.")
    st.stop()

comp_label = st.selectbox(
    "Competition",
    comps.apply(lambda r: f"{r['name']} ({r['date']})", axis=1).tolist(),
)
comp_id = int(comps.iloc[
    comps.apply(lambda r: f"{r['name']} ({r['date']})", axis=1).tolist().index(comp_label)
]["id"])

with database.get_connection() as conn:
    cats = pd.read_sql(
        "SELECT id, name FROM categories WHERE competition_id = ?",
        conn, params=(comp_id,),
    )

if cats.empty:
    st.info("No categories found.")
    st.stop()

cat_name = st.selectbox("Category", cats["name"].tolist())
cat_id = int(cats[cats["name"] == cat_name].iloc[0]["id"])

with database.get_connection() as conn:
    df = pd.read_sql(
        """
        SELECT r.rank, a.name, a.club, a.country,
               r.total_score, r.points_behind, r.penalty
        FROM results r
        JOIN athletes a ON a.id = r.athlete_id
        WHERE r.category_id = ?
        ORDER BY r.rank
        """,
        conn, params=(cat_id,),
    )

st.dataframe(df, use_container_width=True)
```

- [ ] **Step 2: Manual smoke test**

Navigate to Competitions. Select "Delfinek cup (16.05.2026)" → "Beginner L3 FIG (2019-2014)". Expected: 43-row table sorted by rank, with Chromíková Sára at rank 1 with total 60.56.

- [ ] **Step 3: Run full test suite one final time**

```bash
pytest -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add pages/4_competition.py
git commit -m "feat: competition browser"
```

---

## Done

The app is runnable with `streamlit run app.py`. Drop PDFs into `~/aquabely_inbox` and use the Import page to ingest them. All four pages are functional.
