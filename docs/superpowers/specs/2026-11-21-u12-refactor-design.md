# Aquabely Refactor — Multi-Category Support (L3 + U12)

**Date:** 2026-11-21
**Status:** Draft, pending review
**Branch:** `refactor_add_u12`

---

## Overview

Aquabely currently handles one category format (L3). This refactor adds U12 and makes the code ready for further categories and result formats. The refactor starts from a fresh database: no migration of existing data is needed.

Goals:

- Import L3 and U12 result PDFs with one parser per result format.
- Auto-detect the format from the PDF header, with a manual override on import.
- Share athletes across categories, so one athlete has one history.
- Keep every judge mark and reject files that don't match their expected structure.
- Modernise the UI (custom theme and styling) while keeping the existing story: rankings over time, figure scores, judge marks, club medals.
- Keep the whole site behind login (Caddy basic auth). No per-page privacy logic.

Out of scope: team events beyond clubs, OCR, and formats beyond L3 and U12.

---

## Decisions

| Topic | Decision |
|---|---|
| Athletes | Shared across categories. One athlete record links to results in each category. |
| Teams | A team is a club. No separate team entity. |
| Privacy | Entire site behind login (Caddy basic auth). U12 names and birth years are not hidden per page. |
| Parser selection | Auto-detect from the first-page header, with a manual override on the import page. |
| Category model | `categories` = level (`L3`, `U12`). Age group (birth-year range) is a field on each competition entry. "Beginner L3" and "L3" are the same level. |
| Judges | Count varies by competition (7 in one L3 file, 5 in another, 5 in U12). Stored per competition entry, not per category. Every mark is kept. |
| Names | Text extraction loses Czech diacritics in some PDFs (`Kov��ikov�`). Names are stored as extracted. A name-correction table, maintained on the import page, maps extracted names to correct spellings. |
| Figures | Scoped to each competition entry. Figure sets and difficulties can differ between events. |
| UI | Streamlit multi-page app with custom CSS theme and Plotly charts. |
| Data | Fresh database. No migration. |

---

## Data Model (SQLite)

```
clubs
  id, name UNIQUE

categories                        -- level: L3, U12
  id, code UNIQUE, name

competitions
  id, name, date, location,
  source_sha256 UNIQUE,            -- import idempotency
  imported_at

competition_categories            -- one competition + level + age group
  id, competition_id, category_id,
  age_group_label,                 -- e.g. "2015–2019"
  birth_year_from, birth_year_to,
  judges_per_figure,               -- 5 or 7, as found in the PDF
  UNIQUE(competition_id, category_id, age_group_label)

figures                           -- per competition entry
  id, competition_category_id, number, name,
  difficulty NULL                  -- NULL for U12

athletes                          -- shared across categories
  id, name, country, year_of_birth,
  club_id NOT NULL,
  UNIQUE(name, club_id)

name_corrections
  id, raw_name, raw_club, corrected_name,
  UNIQUE(raw_name, raw_club)

results
  id, competition_category_id, athlete_id, club_id,  -- club as entered for that event
  entry_number, rank, total_score, penalty, points_behind,
  UNIQUE(competition_category_id, athlete_id)

figure_results
  id, result_id, figure_id, score, penalty,
  judge_1 … judge_7                -- NULL beyond judges_per_figure

imports                           -- every attempt, including failures
  id, filename, sha256, category_id NULL, status, error, imported_at
```

Notes:

- `results.club_id` records the club for that event, so an athlete who changes clubs keeps accurate history.
- Rankings are computed at query time with window functions (as in the existing athlete-page spec), partitioned by `competition_category_id`.
- U12 `difficulty` is NULL. The UI hides the difficulty column when it is NULL.

---

## Parser Architecture

```
parser/
  models.py          -- ParsedCompetition, ParsedCategory, FigureDef, ParsedResult, FigureResult
  formats/
    base.py          -- FormatParser interface: detect(first_page_text), parse(pdf_path)
    l3.py            -- 4-row athlete blocks, 7 or 5 judges, difficulty in header
    u12.py           -- judge panels in header, numeric figure IDs, 5 judges, no difficulty
  registry.py        -- run all detect() calls; 0 or >1 match is an error
  validate.py        -- structural checks before anything is written
  names.py           -- applies name_corrections to parsed names
```

Format interface:

- `detect(first_page_text) -> bool`: matches on a header signature. L3: `Beginner L3` or `L3 FIG`. U12: `AGE GROUP 12 AND UNDER`.
- `parse(pdf_path) -> ParsedCompetition`: returns the shared models. Nothing downstream depends on format-specific code.

Validation (run before any write; any failure rejects the whole file):

- Each athlete has exactly one row per figure.
- Each figure has the same judge count as the competition's other figures.
- Judge count matches the count printed in the PDF header, where the header states one.
- Figure score is consistent with the average judge mark times difficulty, where difficulty exists (tolerance 0.01). This catches the dropped-judge bug below.
- Ranks are consistent with total scores (ties allowed).

Import flow:

1. Read the file and compute its SHA-256. If `competitions.source_sha256` already exists, refuse.
2. Run `registry.detect`. Show the detected level on the import page, with a dropdown to override.
3. Parse and validate. On error, show the message and log the attempt in `imports`.
4. Apply `name_corrections`. Show any extracted names that still contain replacement characters (`�`) and offer a correction form for each.
5. Write everything in one transaction.

---

## Known Problems to Fix in the Port

- **Dropped judge mark (L3 parser):** for the first sample's F1, the parser keeps 6 of 7 judge marks. The 7 marks average to 6.214, and 6.214 × 1.6 reproduces the printed figure score of 9.944, so the dropped mark is real. The ported parser must keep all marks, and validation must catch any mismatch.
- **Diacritics:** pdfplumber, pdfium, and pypdf all drop the same Czech characters from the U12 PDF. The characters are not in the PDF's text layer, so parsing cannot recover them. The name-correction table is the fix.
- **Name variation:** pdfplumber and pdfium disagree on some name text (for example `Fz.RsI.SCHOV…` vs `z.s. FRISCHOV…`). Corrections are keyed on the extracted name and club, so a fix applies to all imports that produce the same text.

---

## UI

Streamlit multi-page app (`st.navigation`), custom theme in `ui/theme.py`, shared components in `ui/components.py`.

- **Home:** level switch (L3 / U12) and a short summary per level: latest competition, top placings, athletes who moved up the rankings.
- **Import:** upload a PDF, show the detected level with an override, show validation errors, and provide the name-correction form for names containing `�`.
- **Competitions:** pick a competition and age group. Results table with rank, athlete, club, total, penalty, points behind. Expandable figure and judge detail. Difficulty column hidden when NULL.
- **Athletes:** search by name, profile card, and history across all levels. A shared athlete appears in both L3 and U12 if they competed in both. Positions-over-time and score charts as in the existing athlete spec.
- **Clubs:** roster per club, medal tally, and the club's average score per competition.

---

## Testing

- Unit tests for each format's `detect` and `parse`, using the three sample PDFs in `data/` when present. Tests skip with a clear message when the files are absent.
- Tests assert: figure and athlete counts, judge counts per figure, every judge mark retained, and the validation checks.
- No PDFs are committed. `data/` is git-ignored because the samples contain children's names.
- Database tests use an in-memory SQLite database and cover the import transaction (all-or-nothing) and idempotency (duplicate hash refused).
- Manual check: run the app and import all three sample PDFs, then confirm the dashboards and the name-correction flow.

---

## Deployment Changes

- `docs/deployment.md`: remove the "Dashboards: public" statements. The whole site is behind basic auth, matching the `Caddyfile`.
- `Caddyfile`: no change.
- The existing empty `aquabely.db` (created during a smoke test) is discarded. The new schema is created on first run.
