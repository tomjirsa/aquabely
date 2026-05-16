# Aquabely — Artistic Swimming Stats Dashboard

**Date:** 2026-05-16  
**Status:** Approved

---

## Overview

A local Streamlit application that ingests artistic swimming competition result PDFs from rgform.eu/ksis.eu, stores structured data in a SQLite database, and provides dashboards for tracking athlete and club performance across competitions.

---

## Data Source

PDFs exported from `rgform.eu` / `ksis.eu` result pages. Each PDF covers one competition category (e.g. "Beginner L3 FIG (2019-2014)") and contains:

- **Header:** competition name, date, category name
- **Figure definitions:** F1–F4 with name and difficulty value (e.g. "Straight Ballet Leg (1.6)")
- **Result rows:** one athlete per logical row, but physically laid out as 4 sub-rows (one per figure) containing:
  - Rank, country, athlete number, name, club, year of birth
  - Per figure: 7 judge scores, computed figure score, penalty
  - Final total score, points behind leader

PDFs are placed in a configured inbox folder on the local filesystem.

---

## Data Model (SQLite)

```
competitions
  id, name, date, location

categories
  id, competition_id, name

figures
  id, category_id, number (F1/F2/F3/F4), name, difficulty

athletes
  id, name, country, club, year_of_birth
  (deduplicated by name + club; country may update if it changes)

results
  id, athlete_id, category_id, rank, entry_number, total_score, penalty, points_behind

figure_results
  id, result_id, figure_id, score, penalty,
  judge_1, judge_2, judge_3, judge_4, judge_5, judge_6, judge_7
```

Import idempotency: a `imported_files` table stores the filename and SHA-256 hash of each processed PDF so re-importing is safe.

---

## Application Structure

Multi-page Streamlit app (`st.navigation` / `pages/` directory).

### Page 1 — Import

- Reads all PDF files from the configured inbox folder (path set in `config.toml` or a `.env` file)
- Lists files with status: **imported** (green) or **new** (orange), identified by filename hash
- Checkbox to select files for import; "Import selected" button triggers parsing
- Parse errors shown inline per file (bad format, unrecognised structure, etc.)
- On success, shows counts: X athletes, Y results imported

### Page 2 — Athlete Dashboard

- Search box to find an athlete by name (fuzzy match)
- Profile card: name, country, club, year of birth
- Timeline table: all competitions entered, category, rank, total score, date
- Line chart: total score trend over time (x = competition date, y = total score)
- Per-figure score breakdown: grouped bar chart showing F1–F4 scores per competition
- Filter by category name (e.g. show only "Beginner L3" results)

### Page 3 — Club Dashboard

- Dropdown to select club
- Athlete roster with their latest rank and total score per category
- Bar chart: average club score per competition event
- Medal tally: count of 1st/2nd/3rd place results across all competitions
- Cross-competition ranking distribution (histogram of final ranks)

### Page 4 — Competition Browser

- Hierarchical selector: Competition → Category
- Full results table: rank, athlete, club, country, total score, points behind, penalty
- Sortable/filterable columns (Streamlit `st.dataframe` with column config)
- Per-figure score expansion (toggle to show/hide judge scores)

---

## PDF Parsing

Library: `pdfplumber`.

Parsing strategy for each PDF:
1. Extract page 1 text to parse competition name, date, and category from the header lines
2. Parse figure definitions from the sub-header line (pattern: `F1: <name> (<difficulty>)`)
3. Reconstruct athlete blocks — each athlete occupies exactly 4 rows (one per figure). Row 1 carries rank, entry number, name, club, YOB, F1 judge scores, F1 figure score, F1 penalty, total score, and points behind. Rows 2–4 carry only the figure scores and penalties for F2–F4.
4. For each figure row: capture 7 judge scores, figure score, penalty
5. Total score, penalty, points-behind, and athlete metadata are read from row 1 only

Edge cases:
- Multi-page PDFs (handled by iterating all pages)
- Penalty values (0.00 or non-zero — store as-is)
- Duplicate athlete names from different clubs (disambiguated by club name)

---

## Tech Stack

| Component | Library |
|-----------|---------|
| UI | `streamlit` |
| PDF parsing | `pdfplumber` |
| Database | `sqlite3` (stdlib) |
| Data manipulation | `pandas` |
| Charts | `plotly express` |
| Config | `.env` via `python-dotenv` |

Python 3.11+. No external database server required.

---

## Project Layout

```
aquabely/
  app.py                  # Streamlit entry point
  pages/
    1_import.py
    2_athlete.py
    3_club.py
    4_competition.py
  db/
    schema.sql            # DDL for all tables
    database.py           # connection helper, query functions
  parser/
    pdf_parser.py         # PDF → structured dicts
  inbox/                  # drop PDFs here (gitignored)
  aquabely.db             # SQLite file (gitignored)
  requirements.txt
  .env.example            # INBOX_PATH=./inbox
```

---

## Out of Scope

- Web scraping / Cloudflare bypass (PDFs are the data source)
- User authentication
- Multi-user / hosted deployment
- Duo or Team event PDFs (structure may differ — handled as a future extension once Solo parsing is validated)
