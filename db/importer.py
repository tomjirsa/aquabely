from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from parser.models import ParsedCompetition
from parser.validate import validate


class DuplicateImportError(Exception):
    """Raised when a file with the same sha256 was already imported."""


class ValidationFailed(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _log(conn, filename, sha256, status, error=None, category_id=None) -> None:
    conn.execute(
        "INSERT INTO imports(filename, sha256, category_id, status, error, imported_at) "
        "VALUES (?,?,?,?,?,?)",
        (filename, sha256, category_id, status, error, _now()))
    conn.commit()


def import_competition(conn: sqlite3.Connection, comp: ParsedCompetition,
                       sha256: str, filename: str) -> int:
    if conn.execute("SELECT 1 FROM competitions WHERE source_sha256=?", (sha256,)).fetchone():
        _log(conn, filename, sha256, "rejected", "duplicate: file already imported")
        raise DuplicateImportError(sha256)

    report = validate(comp)
    if report.errors:
        _log(conn, filename, sha256, "rejected", "\n".join(report.errors))
        raise ValidationFailed(report.errors)

    cat = conn.execute("SELECT id FROM categories WHERE code=?", (comp.level_code,)).fetchone()
    if cat is None:
        msg = f"unknown category code: {comp.level_code}"
        _log(conn, filename, sha256, "rejected", msg)
        raise ValidationFailed([msg])
    category_id = cat[0]

    try:
        with conn:  # one transaction: commit on success, rollback on error
            cur = conn.execute(
                "INSERT INTO competitions(name, date, location, source_sha256, imported_at) "
                "VALUES (?,?,?,?,?)",
                (comp.name, comp.date, comp.location, sha256, _now()))
            comp_id = cur.lastrowid
            cur = conn.execute(
                "INSERT INTO competition_categories(competition_id, category_id, age_group_label, "
                "birth_year_from, birth_year_to, judges_per_figure) VALUES (?,?,?,?,?,?)",
                (comp_id, category_id, comp.age_group_label, comp.birth_year_from,
                 comp.birth_year_to, comp.judges_per_figure))
            cc_id = cur.lastrowid

            figure_ids: dict[str, int] = {}
            for f in comp.figures:
                cur = conn.execute(
                    "INSERT INTO figures(competition_category_id, number, name, difficulty) "
                    "VALUES (?,?,?,?)", (cc_id, f.number, f.name, f.difficulty))
                figure_ids[f.number] = cur.lastrowid

            for r in comp.results:
                conn.execute("INSERT OR IGNORE INTO clubs(name) VALUES (?)", (r.club,))
                club_id = conn.execute("SELECT id FROM clubs WHERE name=?", (r.club,)).fetchone()[0]
                conn.execute(
                    "INSERT OR IGNORE INTO athletes(name, country, year_of_birth, club_id) "
                    "VALUES (?,?,?,?)", (r.name, r.country, r.year_of_birth, club_id))
                athlete_id = conn.execute(
                    "SELECT id FROM athletes WHERE name=? AND club_id=?", (r.name, club_id)).fetchone()[0]
                cur = conn.execute(
                    "INSERT INTO results(competition_category_id, athlete_id, club_id, entry_number, "
                    "rank, total_score, penalty, points_behind) VALUES (?,?,?,?,?,?,?,?)",
                    (cc_id, athlete_id, club_id, r.entry_number, r.rank, r.total_score,
                     r.penalty, r.points_behind))
                result_id = cur.lastrowid
                for fr in r.figure_results:
                    judges = list(fr.judge_scores) + [None] * (7 - len(fr.judge_scores))
                    conn.execute(
                        "INSERT INTO figure_results(result_id, figure_id, score, penalty, "
                        "judge_1, judge_2, judge_3, judge_4, judge_5, judge_6, judge_7) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (result_id, figure_ids[fr.figure_number], fr.score, fr.penalty, *judges[:7]))
            conn.execute(
                "INSERT INTO imports(filename, sha256, category_id, status, error, imported_at) "
                "VALUES (?,?,?,?,?,?)", (filename, sha256, category_id, "success", None, _now()))
    except Exception as e:
        _log(conn, filename, sha256, "rejected", f"{type(e).__name__}: {e}", category_id)
        raise
    return comp_id
