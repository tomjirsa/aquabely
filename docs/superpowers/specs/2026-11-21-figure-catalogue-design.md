# Figure Catalogue, Judge Marks and Figures Page

**Date:** 2026-11-21
**Status:** Draft, pending review
**Branch:** `refactor_add_u12`
**Source:** `C:\Users\Tom\Downloads\SY_STD_2026.pdf` (Czech technical standards 2026), sections 5 (Seznam figur) and 13 (Obrázky a popis figur)

---

## Overview

Figures are currently identified by the sheet's F-number or by a name matched loosely. The same figure can be F1 in one competition and F2 in another, and two different figures (Straight Ballet Leg, code 106 at U12, and Ballet Leg Single, code 101 at L3) were merged by a name alias. This design makes the official figure catalogue the single source of figure identity, coefficients and descriptions.

Goals:

- Every figure performed in a competition links to one catalogue entry.
- Figure coefficients come from the catalogue, so U12 gets coefficients too.
- The competition and athlete views show each figure's judge marks and its coefficient.
- A new Figures page lists the catalogue by level, with the Czech description, the coefficient, and where each figure was performed.

Out of scope: Youth, Juniors, Seniors and Masters figures, and Beginners L1 and L2. The catalogue format allows adding them later without schema change.

---

## Catalogue

A new table `figure_catalogue`, seeded from the standards document (version 2026):

| Column | Meaning |
|---|---|
| `code` | Official figure code (for example `101`, `106`). Figures without a code use `NULL`. |
| `level` | `L3` or `U12` |
| `name` | English name as printed in section 5 |
| `coefficient` | Difficulty coefficient (REAL) |
| `description_cs` | Czech description from section 13 |
| `source` | `SY_STD_2026 s.5/s.13` |

Seeded entries (L3 and U12 only):

| Level | Code | Name | Coefficient |
|---|---|---|---|
| L3 | 101 | Ballet Leg Single | 1.6 |
| L3 | NULL | From Back Layout Position to Surface Arch Position to Back Layout Position | 1.2 |
| L3 | 316 | Kipnus | 1.4 |
| L3 | NULL | Walkover Front Variant | 1.3 |
| U12 | 106 | Straight Ballet Leg | 1.6 |
| U12 | 301 | Barracuda | 1.8 |
| U12 | 359 | Front Ariana | 2.2 |
| U12 | 348 | Tower | 1.9 |

The U12 figure set in the rulebook also lists "Water Drop", "Swordfish", "Kip" and "Swanita Spinning 180°" for the draw groups. They are seeded for completeness, with `level = U12`.

---

## Matching sheet figures to the catalogue

Each parsed figure is matched in this order:

1. **By code:** if the sheet prints a code (U12 sheets print `106 - Straight Ballet Leg`), match `figure_catalogue.code` for that level.
2. **By alias:** otherwise match a normalised sheet name through an explicit alias table. Confirmed aliases:
   - "Ballet Leg Single" → 101
   - "Straight Ballet Leg" → 101 when the sheet is L3 (confirmed by the controller: the Beginner L3 sheet's F1 is figure 101)
   - "Straight Ballet Leg" → 106 when the sheet is U12 (code match, not alias)
   - "From Back Layout Position to Surface Arch Position to Back Layout Position" and the sheet variant "Back Layout to Surface Arch to Back Layout Position" → the L3 entry without a code
   - "Kipnus" → 316; "Walkover Front Variant" → the L3 entry without a code
3. **No match:** a validation error. The import is rejected and the message names the figure, so the alias table can be extended deliberately.

The alias table lives in one module (`parser/catalogue.py`), next to the seeded data, and is tested.

The old `_FIGURE_NAME_ALIASES` merge of "Straight Ballet Leg" with "Ballet Leg Single" is removed. A U12 "Straight Ballet Leg" and an L3 "Ballet Leg Single" stay separate figures because they are different catalogue codes.

---

## Data model changes

- New table `figure_catalogue` (above), seeded by `schema.sql`.
- `figures` gains `catalogue_id INTEGER REFERENCES figure_catalogue(id)`. It replaces the free-text identity. The existing `number` and `name` columns stay for the sheet's own labels.
- Rankings keep their current partitions (per figure row within a competition category). They are not affected.
- `figures.difficulty` is filled from the catalogue coefficient, so U12 is no longer `NULL`.

---

## Validation changes

- The score check (`parser/validate.py`) uses the catalogue coefficient when the figure is matched, so U12 figures are checked too.
- A figure with no catalogue match is an error (see Matching, step 3).
- The trimmed-mean rule and the 0.05 tolerance stay as they are.

---

## UI

**Competitions page (results detail):** for each athlete, the judge marks for every figure and its coefficient are shown in the detail expander. Figure columns use the catalogue name.

**Athletes page (overview):** the figure table shows, for each competition, the figure rank as now, and below the table a detail section with each figure's judge marks and coefficient. Figure columns use the catalogue name.

**Figures page (new):**
- Level selector (L3 / U12).
- A table of catalogue entries: code (or blank), name, coefficient, Czech description.
- For each figure, a count of performances and the list of competitions where it was performed, linked to the Competitions page.

The page lives in `views/` next to the other pages, and is registered in `app.py` between Competitions and Athletes.

---

## Testing

- `tests/test_catalogue.py`: the seeded entries, the alias table, and the matching order (code first, alias second, error last).
- `tests/test_l3_format.py` and `tests/test_u12_format.py`: every sheet figure resolves to a catalogue entry; the L3 Beginner and Hersalkova F1 both resolve to code 101; U12 F1 resolves to 106 with coefficient 1.6.
- `tests/test_validate.py`: an unmatched figure is an error; the score check uses the catalogue coefficient, so U12 figures are checked.
- `tests/test_queries.py`: judge marks and coefficient are returned per figure; the Figures page query returns the performance count and competition list.
- Browser check: the Competitions and Athletes detail sections and the Figures page, on the scratch database built from the three sample PDFs.

---

## Deployment

No deployment change. The catalogue is seeded by `schema.sql`, which runs on every start and is idempotent (`INSERT OR IGNORE`).
