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
    # sqlite_sequence is an internal SQLite table created by AUTOINCREMENT; exclude it
    tables -= {"sqlite_sequence"}
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
