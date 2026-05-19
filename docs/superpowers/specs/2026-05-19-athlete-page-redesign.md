# Athlete Page Redesign

**Date:** 2026-05-19
**Status:** Approved

## Overview

Split the athlete page into two sections — **Ranking** and **Scores** — and add a ranking table with per-figure color-coded positions and an overall-vs-by-year toggle.

---

## Section 1: Ranking

### Toggle

A `st.radio` at the top of the section with two options:

- **Overall** — ranks computed among all athletes in the same category
- **By year of birth** — ranks computed only among athletes sharing the same `year_of_birth` in the same category

The toggle affects every element in the ranking section.

### Ranking Table

One row per competition the athlete participated in. Columns:

| Column | Content |
|--------|---------|
| Competition | Competition name |
| Date | ISO date (YYYY-MM-DD) |
| Overall / By-year rank | Athlete's rank; column header updates to reflect the active toggle mode |
| F1, F2, … Fn | Athlete's rank for that figure, color-coded |

Figure rank cell coloring (relative to the athlete's overall rank in that same competition):

- **Green** (`#1a4a2e` bg / `#57cc99` text) — figure rank < overall rank (performed better on this figure)
- **Red** (`#4a1a1a` bg / `#e07070` text) — figure rank > overall rank (performed worse)
- **Grey** (`#2a2a2a` bg / `#888888` text) — figure rank = overall rank (equal)

Implemented via `pandas.io.formats.style.Styler` applied to a pivoted DataFrame.

Competitions sorted oldest → newest (ascending date).

### Positions Over Time Chart

Plotly line chart:

- X-axis: competition date (chronological, oldest left)
- Y-axis: rank, **inverted** (`autorange='reversed'`) so 1st place is at the top
- Series:
  - Overall rank — thick solid line
  - F1, F2, … Fn ranks — thinner dashed lines, one per figure number
- Toggle switches which rank values are plotted (overall or by-year)
- `category_orders` ensures chronological x-axis order

---

## Section 2: Scores

Move the existing plots under a `st.subheader("Scores")` header. No changes to logic, no year grouping. Current plots:

1. Total score over time (line)
2. Figure scores over time (line, one series per figure)
3. Figure scores per competition (grouped bar)
4. Judge marks per figure (dropdown → grouped bar)

---

## Data & Queries

**No schema changes.** All ranking is computed at query time using SQLite window functions (available in SQLite 3.25+; Python 3.12 ships with 3.39+).

### Core ranking query

```sql
WITH all_ranks AS (
    SELECT
        r.id          AS result_id,
        r.athlete_id,
        c.name        AS competition,
        c.date,
        RANK() OVER (PARTITION BY cat.id
                     ORDER BY r.total_score DESC)                      AS rank_overall,
        RANK() OVER (PARTITION BY cat.id, a.year_of_birth
                     ORDER BY r.total_score DESC)                      AS rank_by_year
    FROM results r
    JOIN athletes a   ON a.id  = r.athlete_id
    JOIN categories cat ON cat.id = r.category_id
    JOIN competitions c ON c.id  = cat.competition_id
),
fig_ranks AS (
    SELECT
        fr.result_id,
        f.number      AS figure_number,
        RANK() OVER (PARTITION BY f.category_id
                     ORDER BY fr.score DESC)                           AS rank_overall,
        RANK() OVER (PARTITION BY f.category_id, a.year_of_birth
                     ORDER BY fr.score DESC)                           AS rank_by_year
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
```

### Python pivot & style

1. Query returns one row per (competition, figure). 
2. Select the active rank columns based on toggle (`rank_overall` or `rank_by_year`, `fig_rank_overall` or `fig_rank_by_year`).
3. Pivot: `df.pivot(index=["competition","date","overall_rank"], columns="figure_number", values="fig_rank")`.
4. Apply `Styler.applymap` to figure rank columns: compare cell value to `overall_rank` on the same row and return the appropriate CSS background/color.
5. Render with `st.dataframe(styled, use_container_width=True)`.

---

## File Changes

| File | Change |
|------|--------|
| `pages/2_athlete.py` | Full rewrite — add ranking section with toggle, table, chart; wrap existing plots in Scores section |
| `db/database.py` | No changes |
| `db/schema.sql` | No changes |

---

## Out of Scope

- Ranking for the Scores section (scores are shown as raw values, not positions)
- Club or competition pages
