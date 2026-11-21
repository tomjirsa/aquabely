import sqlite3
import pytest
from db.database import init_schema

TABLES = {"clubs", "categories", "competitions", "competition_categories",
"figures", "athletes", "results",
          "figure_results", "imports", "figure_catalogue"}


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    init_schema(c)
    yield c
    c.close()


def test_creates_all_tables(conn):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
             if not r[0].startswith("sqlite_")}
    assert names == TABLES


def test_duplicate_source_sha256_is_rejected(conn):
    conn.execute("INSERT INTO competitions(name, date, location, source_sha256, imported_at) "
                 "VALUES ('A','2026-01-01','','abc','2026-01-02')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO competitions(name, date, location, source_sha256, imported_at) "
                     "VALUES ('B','2026-01-01','','abc','2026-01-02')")


def test_one_result_per_athlete_per_competition_category(conn):
    # Set up the parent rows directly, then insert the duplicate result.
    conn.execute("INSERT INTO clubs(id, name) VALUES (1,'C')")
    conn.execute("INSERT INTO athletes(id, name, country, year_of_birth, club_id) VALUES (1,'N','CZE',2016,1)")
    conn.execute("INSERT INTO competitions(id, name, date, location, source_sha256, imported_at) "
                 "VALUES (1,'A','2026-01-01','','h','t')")
    conn.execute("INSERT INTO competition_categories(id, competition_id, category_id, age_group_label, "
                 "birth_year_from, birth_year_to, judges_per_figure) VALUES (1,1,1,'2014–2019',2014,2019,7)")
    conn.execute("INSERT INTO results(competition_category_id, athlete_id, club_id, rank, total_score, penalty, points_behind) "
                 "VALUES (1,1,1,1,50,0,0)")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO results(competition_category_id, athlete_id, club_id, rank, total_score, penalty, points_behind) "
                     "VALUES (1,1,1,2,49,0,0)")


def test_fresh_db_has_level_categories():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    assert [r[0] for r in c.execute("SELECT code FROM categories ORDER BY code")] == ["L3", "U12"]
    c.close()


def test_init_schema_is_idempotent():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    init_schema(c)
    assert c.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 2
    c.close()


def test_old_schema_database_is_refused():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE categories(id INTEGER PRIMARY KEY, name TEXT)")
    with pytest.raises(RuntimeError, match="old schema"):
        init_schema(c)
    c.close()
