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
