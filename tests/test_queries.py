import sqlite3
import pytest
from db.database import init_schema
from db.importer import import_competition
from db.queries import competitions_for_level, results_for, club_medals, athlete_rankings
from tests.test_importer import make  # reuse builder


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    c.execute("INSERT INTO categories(code, name) VALUES ('L3','Level 3'), ('U12','Under 12')")
    import_competition(c, make(level="L3", name="A", club="C"), sha256="q1", filename="a.pdf")
    import_competition(c, make(level="U12", name="B", club="C"), sha256="q2", filename="b.pdf")
    yield c


def test_competitions_filtered_by_level(conn):
    df = competitions_for_level(conn, "L3")
    assert len(df) == 1 and df.iloc[0]["age_group_label"] == "2014–2019"


def test_results_for_one_competition(conn):
    cc = competitions_for_level(conn, "L3").iloc[0]["competition_category_id"]
    df = results_for(conn, int(cc))
    assert list(df["name"]) == ["A"]


def test_medals_count_top_three(conn):
    club_id = conn.execute("SELECT id FROM clubs WHERE name='C'").fetchone()[0]
    df = club_medals(conn, club_id)
    assert int(df.loc[df["place"] == 1, "count"].iloc[0]) == 2


def test_athlete_rankings_one_row_per_competition_figure(conn):
    aid = conn.execute("SELECT id FROM athletes WHERE name='A'").fetchone()[0]
    df = athlete_rankings(conn, aid)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["figure_number"] == "F1"
    assert row["rank_overall"] == 1 and row["fig_rank_by_year"] == 1
