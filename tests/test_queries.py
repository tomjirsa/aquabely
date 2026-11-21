import sqlite3
import pytest
from db.database import init_schema
from db.importer import import_competition
from db.queries import competitions_for_level, results_for, club_medals, athlete_rankings
from parser.models import FigureDef, FigureResult, ParsedCompetition, ParsedResult
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
    assert df.iloc[0]["rank"] == 1 and df.iloc[0]["total_score"] == 50.0


def test_medals_count_top_three(conn):
    club_id = conn.execute("SELECT id FROM clubs WHERE name='C'").fetchone()[0]
    df = club_medals(conn, club_id)
    assert int(df.loc[df["place"] == 1, "count"].iloc[0]) == 2


def _comp(date, rows, club="C"):
    """rows: (rank, name, year_of_birth, total_score)."""
    results = [ParsedResult(rk, i + 1, nm, club, "CZE", yob, sc, 0.0, 0.0,
                            [FigureResult("F1", [5.0] * 5, sc, 0.0)])
               for i, (rk, nm, yob, sc) in enumerate(rows)]
    return ParsedCompetition("Cup", date, "", "L3", "2014–2019", 2014, 2019,
                             5, [FigureDef("F1", "Ballet", None)], results)


def test_club_medals_places_two_and_three_and_excludes_fourth_plus():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    c.execute("INSERT INTO categories(code, name) VALUES ('L3','Level 3')")
    import_competition(c, _comp("2026-01-01", [(1, "P", 2016, 90.0), (2, "Q", 2016, 80.0),
                                               (3, "R", 2016, 70.0), (4, "S", 2016, 60.0)]),
                       sha256="m1", filename="m1.pdf")
    import_competition(c, _comp("2026-02-01", [(1, "P", 2016, 90.0), (2, "Q", 2016, 80.0),
                                               (3, "R", 2016, 70.0), (4, "S", 2016, 60.0),
                                               (5, "T", 2016, 50.0)]),
                       sha256="m2", filename="m2.pdf")
    import_competition(c, _comp("2026-03-01", [(2, "Q", 2016, 80.0), (3, "R", 2016, 70.0),
                                               (4, "S", 2016, 60.0)]),
                       sha256="m3", filename="m3.pdf")
    club_id = c.execute("SELECT id FROM clubs WHERE name='C'").fetchone()[0]
    df = club_medals(c, club_id)
    counts = {int(p): int(n) for p, n in zip(df["place"], df["count"])}
    assert counts == {1: 2, 2: 3, 3: 3}
    assert (df["place"] > 3).sum() == 0


def test_athlete_rankings_one_row_per_competition_figure(conn):
    aid = conn.execute("SELECT id FROM athletes WHERE name='A'").fetchone()[0]
    df = athlete_rankings(conn, aid)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["figure_number"] == "F1"
    assert row["rank_overall"] == 1 and row["fig_rank_by_year"] == 1


def test_rankings_partition_by_category_and_birth_year():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    c.execute("INSERT INTO categories(code, name) VALUES ('L3','Level 3')")
    # Competition 1: Y (2015) 70, Z (2016) 60, X (2016) 50
    import_competition(c, _comp("2026-01-01", [(1, "Y", 2015, 70.0), (2, "Z", 2016, 60.0),
                                               (3, "X", 2016, 50.0)]),
                       sha256="r1", filename="r1.pdf")
    # Competition 2: X 80, Z 60, Y 40 -- order reversed vs competition 1
    import_competition(c, _comp("2026-02-01", [(1, "X", 2016, 80.0), (2, "Z", 2016, 60.0),
                                               (3, "Y", 2015, 40.0)]),
                       sha256="r2", filename="r2.pdf")

    def ranks(name):
        aid = c.execute("SELECT id FROM athletes WHERE name=?", (name,)).fetchone()[0]
        df = athlete_rankings(c, aid)
        assert len(df) == 2
        return [(int(r.rank_overall), int(r.rank_by_year),
                 int(r.fig_rank_overall), int(r.fig_rank_by_year)) for r in df.itertuples()]

    # (rank_overall, rank_by_year, fig_rank_overall, fig_rank_by_year) per competition, by date
    assert ranks("Y") == [(1, 1, 1, 1), (3, 1, 3, 1)]
    assert ranks("Z") == [(2, 1, 2, 1), (2, 2, 2, 2)]
    assert ranks("X") == [(3, 2, 3, 2), (1, 1, 1, 1)]
