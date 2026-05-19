# Athlete Page Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the athlete page into a Ranking section (toggle overall/by-year, color-coded table, positions chart) and a Scores section (existing plots, reorganised).

**Architecture:** SQLite window functions compute all rankings at query time — no schema changes. A pure-function helpers module (`pages/_athlete.py`) contains testable logic; `pages/2_athlete.py` is the Streamlit page. A new `database.get_athlete_rankings()` function runs the CTE query.

**Tech Stack:** Python 3.12, SQLite 3.39+ (window functions), pandas (pivot + Styler), Plotly Express, Streamlit.

---

## Task 1: Add `get_athlete_rankings` to `db/database.py`

**Files:**
- Modify: `db/database.py`
- Modify: `tests/conftest.py`
- Modify: `tests/test_database.py`

- [ ] **Step 1: Add `two_athlete_pdf` fixture to `tests/conftest.py`**

Open `tests/conftest.py` and append this fixture. Alice (rank 1) scores best in F1; Bob (rank 2) scores best in F2. Same year-of-birth so by-year rank equals overall rank.

```python
@pytest.fixture
def two_athlete_pdf():
    return ParsedPDF(
        competition_name="Rank Cup",
        date="2026-03-01",
        category_name="Beginner L1",
        figures=[
            FigureDef("F1", "Ballet Leg", 1.6),
            FigureDef("F2", "Kipnus", 1.4),
        ],
        results=[
            AthleteResult(
                rank=1, entry_number=1,
                name="Alice", club="Club A", country="CZE", yob=2015,
                total_score=70.0, penalty=0.0, points_behind=0.0,
                figure_results=[
                    FigureResult("F1", [7.0] * 7, 11.2, 0.0),
                    FigureResult("F2", [6.0] * 7, 8.4, 0.0),
                ],
            ),
            AthleteResult(
                rank=2, entry_number=2,
                name="Bob", club="Club B", country="CZE", yob=2015,
                total_score=60.0, penalty=0.0, points_behind=0.0,
                figure_results=[
                    FigureResult("F1", [5.0] * 7, 8.0, 0.0),
                    FigureResult("F2", [8.0] * 7, 11.2, 0.0),
                ],
            ),
        ],
    )
```

- [ ] **Step 2: Write failing tests in `tests/test_database.py`**

Append these two tests:

```python
def test_get_athlete_rankings_returns_correct_overall_rank(two_athlete_pdf):
    database.init_schema()
    database.insert_pdf_result(two_athlete_pdf, "rank.pdf", "rankhash1")
    with database.get_connection() as conn:
        alice_id = conn.execute(
            "SELECT id FROM athletes WHERE name='Alice'"
        ).fetchone()["id"]
    df = database.get_athlete_rankings(alice_id)
    assert len(df) == 2  # one row per figure
    f1 = df[df["figure_number"] == "F1"].iloc[0]
    f2 = df[df["figure_number"] == "F2"].iloc[0]
    assert f1["rank_overall"] == 1   # Alice ranked 1st overall
    assert f1["fig_rank_overall"] == 1  # Alice best in F1
    assert f2["fig_rank_overall"] == 2  # Alice 2nd in F2 (Bob scored higher)


def test_get_athlete_rankings_by_year_equals_overall_when_same_yob(two_athlete_pdf):
    database.init_schema()
    database.insert_pdf_result(two_athlete_pdf, "rank.pdf", "rankhash2")
    with database.get_connection() as conn:
        alice_id = conn.execute(
            "SELECT id FROM athletes WHERE name='Alice'"
        ).fetchone()["id"]
    df = database.get_athlete_rankings(alice_id)
    # Both athletes share yob=2015, so by-year == overall
    assert (df["rank_overall"] == df["rank_by_year"]).all()
    assert (df["fig_rank_overall"] == df["fig_rank_by_year"]).all()
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
cd /Users/tjirsik/Repository/aquabely && .venv/bin/pytest tests/test_database.py::test_get_athlete_rankings_returns_correct_overall_rank tests/test_database.py::test_get_athlete_rankings_by_year_equals_overall_when_same_yob -v
```

Expected: `AttributeError: module 'db.database' has no attribute 'get_athlete_rankings'`

- [ ] **Step 4: Add `import pandas as pd` and `get_athlete_rankings` to `db/database.py`**

Add `import pandas as pd` at the top of the imports block. Then append this function at the end of the file:

```python
import pandas as pd  # add to imports at top of file


def get_athlete_rankings(athlete_id: int) -> "pd.DataFrame":
    sql = """
    WITH all_ranks AS (
        SELECT
            r.id          AS result_id,
            r.athlete_id,
            c.name        AS competition,
            c.date,
            RANK() OVER (PARTITION BY cat.id
                         ORDER BY r.total_score DESC)         AS rank_overall,
            RANK() OVER (PARTITION BY cat.id, a.year_of_birth
                         ORDER BY r.total_score DESC)         AS rank_by_year
        FROM results r
        JOIN athletes   a   ON a.id   = r.athlete_id
        JOIN categories cat ON cat.id = r.category_id
        JOIN competitions c ON c.id   = cat.competition_id
    ),
    fig_ranks AS (
        SELECT
            fr.result_id,
            f.number AS figure_number,
            RANK() OVER (PARTITION BY f.category_id
                         ORDER BY fr.score DESC)              AS rank_overall,
            RANK() OVER (PARTITION BY f.category_id, a.year_of_birth
                         ORDER BY fr.score DESC)              AS rank_by_year
        FROM figure_results fr
        JOIN figures  f ON f.id  = fr.figure_id
        JOIN results  r ON r.id  = fr.result_id
        JOIN athletes a ON a.id  = r.athlete_id
    )
    SELECT
        ar.competition,
        ar.date,
        ar.rank_overall,
        ar.rank_by_year,
        fr.figure_number,
        fr.rank_overall  AS fig_rank_overall,
        fr.rank_by_year  AS fig_rank_by_year
    FROM all_ranks ar
    JOIN fig_ranks fr ON fr.result_id = ar.result_id
    WHERE ar.athlete_id = ?
    ORDER BY ar.date, fr.figure_number
    """
    with get_connection() as conn:
        return pd.read_sql(sql, conn, params=(athlete_id,))
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd /Users/tjirsik/Repository/aquabely && .venv/bin/pytest tests/test_database.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add db/database.py tests/conftest.py tests/test_database.py
git commit -m "feat: add get_athlete_rankings window-function query"
```

---

## Task 2: Add pure ranking helpers to `pages/_athlete.py`

**Files:**
- Create: `pages/_athlete.py`
- Create: `tests/test_athlete_ranking.py`

- [ ] **Step 1: Write failing tests in `tests/test_athlete_ranking.py`**

```python
import pandas as pd
import pytest
from pages._athlete import _build_ranking_table, _style_rank_row


@pytest.fixture
def raw_rank_df():
    return pd.DataFrame([
        {"competition": "Cup A", "date": "2026-01-01",
         "rank_overall": 3, "rank_by_year": 2,
         "figure_number": "F1", "fig_rank_overall": 1, "fig_rank_by_year": 1},
        {"competition": "Cup A", "date": "2026-01-01",
         "rank_overall": 3, "rank_by_year": 2,
         "figure_number": "F2", "fig_rank_overall": 5, "fig_rank_by_year": 4},
        {"competition": "Cup A", "date": "2026-01-01",
         "rank_overall": 3, "rank_by_year": 2,
         "figure_number": "F3", "fig_rank_overall": 3, "fig_rank_by_year": 2},
    ])


def test_build_ranking_table_overall_selects_correct_columns(raw_rank_df):
    wide, fig_cols = _build_ranking_table(raw_rank_df, by_year=False)
    assert "overall_rank" in wide.columns
    assert wide.iloc[0]["overall_rank"] == 3
    assert set(fig_cols) == {"F1", "F2", "F3"}
    assert wide.iloc[0]["F1"] == 1
    assert wide.iloc[0]["F2"] == 5


def test_build_ranking_table_by_year_selects_correct_columns(raw_rank_df):
    wide, fig_cols = _build_ranking_table(raw_rank_df, by_year=True)
    assert wide.iloc[0]["overall_rank"] == 2  # rank_by_year
    assert wide.iloc[0]["F1"] == 1
    assert wide.iloc[0]["F2"] == 4            # fig_rank_by_year


def test_style_rank_row_green_when_figure_better():
    row = pd.Series({"competition": "Cup", "date": "2026-01-01",
                     "overall_rank": 3, "F1": 1, "F2": 5, "F3": 3})
    styles = _style_rank_row(row, ["F1", "F2", "F3"])
    assert styles[3] == "background-color: #1a4a2e; color: #57cc99"  # F1 < 3


def test_style_rank_row_red_when_figure_worse():
    row = pd.Series({"competition": "Cup", "date": "2026-01-01",
                     "overall_rank": 3, "F1": 1, "F2": 5, "F3": 3})
    styles = _style_rank_row(row, ["F1", "F2", "F3"])
    assert styles[4] == "background-color: #4a1a1a; color: #e07070"  # F2 > 3


def test_style_rank_row_grey_when_figure_equal():
    row = pd.Series({"competition": "Cup", "date": "2026-01-01",
                     "overall_rank": 3, "F1": 1, "F2": 5, "F3": 3})
    styles = _style_rank_row(row, ["F1", "F2", "F3"])
    assert styles[5] == "background-color: #2a2a2a; color: #888888"  # F3 == 3


def test_style_rank_row_empty_for_non_figure_columns():
    row = pd.Series({"competition": "Cup", "date": "2026-01-01",
                     "overall_rank": 3, "F1": 1})
    styles = _style_rank_row(row, ["F1"])
    assert styles[0] == ""  # competition
    assert styles[1] == ""  # date
    assert styles[2] == ""  # overall_rank


def test_style_rank_row_empty_for_nan():
    row = pd.Series({"competition": "Cup", "date": "2026-01-01",
                     "overall_rank": 3, "F1": float("nan")})
    styles = _style_rank_row(row, ["F1"])
    assert styles[3] == ""
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/tjirsik/Repository/aquabely && .venv/bin/pytest tests/test_athlete_ranking.py -v
```

Expected: `ModuleNotFoundError: No module named 'pages._athlete'`

- [ ] **Step 3: Create `pages/_athlete.py`**

```python
import pandas as pd


def _build_ranking_table(rank_df: pd.DataFrame, by_year: bool) -> tuple[pd.DataFrame, list[str]]:
    rank_col = "rank_by_year" if by_year else "rank_overall"
    fig_rank_col = "fig_rank_by_year" if by_year else "fig_rank_overall"
    df = rank_df[["competition", "date", rank_col, "figure_number", fig_rank_col]].copy()
    df = df.rename(columns={rank_col: "overall_rank", fig_rank_col: "fig_rank"})
    wide = df.pivot_table(
        index=["competition", "date", "overall_rank"],
        columns="figure_number",
        values="fig_rank",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    wide = wide.sort_values("date").reset_index(drop=True)
    fig_cols = [c for c in wide.columns if str(c).startswith("F")]
    return wide, fig_cols


def _style_rank_row(row: pd.Series, fig_cols: list[str]) -> list[str]:
    overall = row["overall_rank"]
    styles = []
    for col in row.index:
        if col not in fig_cols or pd.isna(row[col]):
            styles.append("")
        elif int(row[col]) < int(overall):
            styles.append("background-color: #1a4a2e; color: #57cc99")
        elif int(row[col]) > int(overall):
            styles.append("background-color: #4a1a1a; color: #e07070")
        else:
            styles.append("background-color: #2a2a2a; color: #888888")
    return styles
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd /Users/tjirsik/Repository/aquabely && .venv/bin/pytest tests/test_athlete_ranking.py -v
```

Expected: all 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add pages/_athlete.py tests/test_athlete_ranking.py
git commit -m "feat: add ranking table helpers with tests"
```

---

## Task 3: Rewrite `pages/2_athlete.py` with Ranking and Scores sections

**Files:**
- Modify: `pages/2_athlete.py`

- [ ] **Step 1: Replace the file with the full implementation**

Write the complete content below to `pages/2_athlete.py`:

```python
import pandas as pd
import plotly.express as px
import streamlit as st

import db.database as database
from pages._athlete import _build_ranking_table, _style_rank_row

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
athlete_id = int(row["id"])

# ── Ranking ──────────────────────────────────────────────────────────────────

st.subheader("Ranking")
mode = st.radio("Ranking mode", ["Overall", "By year of birth"], horizontal=True)
by_year = mode == "By year of birth"

rank_df = database.get_athlete_rankings(athlete_id)

if rank_df.empty:
    st.info("No ranking data available.")
else:
    wide, fig_cols = _build_ranking_table(rank_df, by_year)
    rank_label = "By-year rank" if by_year else "Overall rank"

    display = wide.rename(columns={"overall_rank": rank_label})

    def _style_display_row(row):
        return _style_rank_row(row.rename({rank_label: "overall_rank"}), fig_cols)

    styled = (
        display.style
        .apply(_style_display_row, axis=1)
        .format(na_rep="—", subset=fig_cols)
    )
    st.dataframe(styled, use_container_width=True)

    chart_df = wide.melt(
        id_vars=["competition", "date"],
        value_vars=["overall_rank"] + fig_cols,
        var_name="series",
        value_name="rank",
    )
    chart_df["series"] = chart_df["series"].replace("overall_rank", "Overall")
    date_order = list(dict.fromkeys(chart_df.sort_values("date")["date"]))

    fig_pos = px.line(
        chart_df.dropna(subset=["rank"]),
        x="date",
        y="rank",
        color="series",
        markers=True,
        title="Positions over time",
        labels={"rank": "Rank", "date": "Date", "series": ""},
        category_orders={"date": date_order},
    )
    fig_pos.update_yaxes(autorange="reversed", title="Rank (lower = better)")
    for trace in fig_pos.data:
        if trace.name == "Overall":
            trace.line.width = 3
        else:
            trace.line.dash = "dash"
            trace.line.width = 1.5
    st.plotly_chart(fig_pos, use_container_width=True)

# ── Scores ────────────────────────────────────────────────────────────────────

st.subheader("Scores")

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

df = df.sort_values("date")
fig = px.line(
    df, x="date", y="total_score", markers=True,
    title="Total score over time",
    labels={"total_score": "Score", "date": "Date"},
)
st.plotly_chart(fig, use_container_width=True)

with database.get_connection() as conn:
    fig_df = pd.read_sql(
        """
        SELECT c.date, c.name AS competition, f.number AS figure,
               f.name AS figure_name, fr.score AS figure_score
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
    fig_df = fig_df.sort_values("date")
    fig_df["figure_label"] = fig_df["figure"] + ": " + fig_df["figure_name"]
    fig_order = sorted(
        fig_df["figure_label"].unique(),
        key=lambda x: int(x[1:x.index(":")]),
    )
    comp_order = list(dict.fromkeys(fig_df.sort_values("date")["competition"]))

    fig2 = px.line(
        fig_df, x="date", y="figure_score", color="figure_label", markers=True,
        title="Figure scores over time",
        labels={"figure_score": "Score", "date": "Date", "figure_label": "Figure"},
        category_orders={"figure_label": fig_order},
    )
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.bar(
        fig_df, x="competition", y="figure_score", color="figure_label",
        barmode="group", title="Figure scores per competition",
        labels={"figure_label": "Figure", "figure_score": "Score"},
        category_orders={"figure_label": fig_order, "competition": comp_order},
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Judge marks per figure")
    competitions = sorted(fig_df["competition"].unique())
    selected_comp = st.selectbox("Competition", competitions, key="judge_marks_comp")

    with database.get_connection() as conn:
        marks_df = pd.read_sql(
            """
            SELECT f.number AS figure, f.name AS figure_name,
                   fr.judge_1, fr.judge_2, fr.judge_3, fr.judge_4,
                   fr.judge_5, fr.judge_6, fr.judge_7
            FROM figure_results fr
            JOIN results r ON r.id = fr.result_id
            JOIN figures f ON f.id = fr.figure_id
            JOIN athletes a ON a.id = r.athlete_id
            JOIN categories cat ON cat.id = r.category_id
            JOIN competitions c ON c.id = cat.competition_id
            WHERE a.name = ? AND c.name = ?
            ORDER BY f.number
            """,
            conn,
            params=(name, selected_comp),
        )

    judge_cols = [
        "judge_1", "judge_2", "judge_3", "judge_4",
        "judge_5", "judge_6", "judge_7",
    ]
    marks_df = marks_df.melt(
        id_vars=["figure", "figure_name"],
        value_vars=[c for c in judge_cols if marks_df[c].notna().any()],
        var_name="judge",
        value_name="mark",
    ).dropna(subset=["mark"])
    marks_df["figure_label"] = marks_df["figure"] + ": " + marks_df["figure_name"]
    marks_df["judge"] = marks_df["judge"].str.replace("judge_", "J", regex=False)

    fig4 = px.bar(
        marks_df, x="figure_label", y="mark", color="judge", barmode="group",
        title=f"Judge marks — {selected_comp}",
        labels={"figure_label": "Figure", "mark": "Mark", "judge": "Judge"},
        category_orders={
            "figure_label": sorted(
                marks_df["figure_label"].unique(),
                key=lambda x: int(x[1:x.index(":")]),
            )
        },
    )
    fig4.update_layout(yaxis_range=[0, 10])
    st.plotly_chart(fig4, use_container_width=True)
```

- [ ] **Step 2: Run the full test suite**

```bash
cd /Users/tjirsik/Repository/aquabely && .venv/bin/pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 3: Smoke-test the page locally**

```bash
cd /Users/tjirsik/Repository/aquabely && .venv/bin/streamlit run app.py
```

Navigate to the Athletes page. Verify:
- "Ranking" subheader and mode radio appear above the table
- Table shows color-coded figure rank cells (green/red/grey)
- Column header reads "Overall rank" or "By-year rank" matching the radio
- Positions chart shows inverted y-axis with Overall as thick line, figure ranks as dashed
- "Scores" subheader appears below, existing charts unchanged

- [ ] **Step 4: Commit**

```bash
git add pages/2_athlete.py
git commit -m "feat: athlete page ranking section with color-coded table and positions chart"
```
