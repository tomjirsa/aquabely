import dataclasses
import sqlite3
import pandas as pd
import pytest
from db.database import init_schema
from db.importer import import_competition
from db.queries import (competitions_for_level, results_for, club_medals, athlete_rankings,
                        athlete_list, athlete_history, athlete_overall_ranks,
                        athlete_figure_scores, result_judge_marks, level_athlete_count,
                        club_list, club_roster, club_avg_scores, competition_figures,
                        competition_judge_detail, competition_figure_detail,
                        athlete_figure_detail, catalogue_figures)
from parser.models import FigureDef, FigureResult, ParsedCompetition, ParsedResult
from tests.test_importer import make  # reuse builder


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    init_schema(c)
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
                             5, [FigureDef("F1", "Straight Ballet Leg", None, "106")], results)


def test_club_medals_places_two_and_three_and_excludes_fourth_plus():
    c = sqlite3.connect(":memory:")
    init_schema(c)
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


def _aid(conn, name):
    return conn.execute("SELECT id FROM athletes WHERE name=?", (name,)).fetchone()[0]


def test_athlete_list(conn):
    df = athlete_list(conn)
    assert list(df["name"]) == ["A", "B"]
    row = df.iloc[0]
    assert row["club"] == "C" and row["country"] == "CZE" and row["year_of_birth"] == 2016


def test_athlete_history(conn):
    df = athlete_history(conn, _aid(conn, "A"))
    assert len(df) == 1
    row = df.iloc[0]
    assert (row["level"], row["competition"], row["date"]) == ("L3", "Cup", "2026-01-01")
    assert row["age_group"] == "2014–2019"
    assert row["rank"] == 1 and row["total_score"] == 50.0
    assert row["result_id"] > 0 and row["competition_category_id"] > 0


def test_level_athlete_count(conn):
    assert level_athlete_count(conn, "L3") == 1
    assert level_athlete_count(conn, "U12") == 1


def test_club_list_and_roster(conn):
    clubs = club_list(conn)
    assert list(clubs["name"]) == ["C"]
    df = club_roster(conn, int(clubs.iloc[0]["id"]))
    assert list(df["name"]) == ["A", "B"]
    assert list(df["year_of_birth"]) == [2016, 2016] and list(df["country"]) == ["CZE", "CZE"]


def test_club_avg_scores():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    import_competition(c, _comp("2026-01-01", [(1, "P", 2016, 90.0), (2, "Q", 2016, 70.0)]),
                       sha256="v1", filename="v1.pdf")
    import_competition(c, _comp("2026-02-01", [(1, "P", 2016, 80.0)]),
                       sha256="v2", filename="v2.pdf")
    club_id = c.execute("SELECT id FROM clubs WHERE name='C'").fetchone()[0]
    df = club_avg_scores(c, club_id)
    assert list(df["date"]) == ["2026-01-01", "2026-02-01"]
    assert list(df["avg_total"]) == [80.0, 80.0]


def test_competition_figures(conn):
    cc = int(competitions_for_level(conn, "L3").iloc[0]["competition_category_id"])
    df = competition_figures(conn, cc)
    assert list(df["number"]) == ["F1"] and list(df["name"]) == ["Ballet Leg Single"]


def test_competition_judge_detail(conn):
    cc = int(competitions_for_level(conn, "L3").iloc[0]["competition_category_id"])
    df = competition_judge_detail(conn, cc)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["athlete"] == "A" and row["figure"] == "F1" and row["score"] == 5.0
    assert row["judge_5"] == 5.0 and df["judge_6"].isna().all()


def test_athlete_figure_scores_and_judge_marks(conn):
    aid = _aid(conn, "A")
    df = athlete_figure_scores(conn, aid)
    assert len(df) == 1
    assert (df.iloc[0]["figure_name"], df.iloc[0]["figure_score"]) == ("Ballet Leg Single", 5.0)
    rid = int(athlete_history(conn, aid).iloc[0]["result_id"])
    marks = result_judge_marks(conn, rid)
    assert len(marks) == 1 and marks.iloc[0]["figure_name"] == "Ballet Leg Single"
    assert marks.iloc[0]["judge_1"] == 5.0 and pd.isna(marks.iloc[0]["judge_7"])


def test_athlete_overall_ranks_without_figure_results():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    comp = _comp("2026-01-01", [(1, "P", 2016, 90.0), (2, "Q", 2016, 70.0)])
    comp = dataclasses.replace(
        comp, figures=[],
        results=[dataclasses.replace(r, figure_results=[]) for r in comp.results])
    import_competition(c, comp, sha256="nf", filename="nf.pdf")
    q = c.execute("SELECT id FROM athletes WHERE name='Q'").fetchone()[0]
    assert athlete_rankings(c, q).empty
    df = athlete_overall_ranks(c, q)
    assert len(df) == 1
    assert df.iloc[0]["rank_overall"] == 2 and df.iloc[0]["rank_by_year"] == 2
    assert df.iloc[0]["date"] == "2026-01-01"


def _field_conn():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    # one category, 3 athletes: two born 2016, one born 2015
    import_competition(c, _comp("2026-01-01", [(1, "Y", 2015, 70.0), (2, "Z", 2016, 60.0),
                                               (3, "X", 2016, 50.0)]),
                       sha256="fs1", filename="fs1.pdf")
    return c


def test_athlete_history_field_size_counts_category_results():
    c = _field_conn()
    for name in ("X", "Y", "Z"):
        df = athlete_history(c, _aid(c, name))
        assert list(df["field_size"]) == [3]
        assert "rank" in df.columns and "total_score" in df.columns


def test_athlete_rankings_field_size_by_year_counts_same_birth_year_only():
    c = _field_conn()
    df = athlete_rankings(c, _aid(c, "X"))
    assert set(df["field_size"]) == {3}
    assert set(df["field_size_by_year"]) == {2}
    df = athlete_rankings(c, _aid(c, "Y"))
    assert set(df["field_size"]) == {3} and set(df["field_size_by_year"]) == {1}


def test_athlete_overall_ranks_field_sizes():
    c = _field_conn()
    df = athlete_overall_ranks(c, _aid(c, "Z"))
    assert df.iloc[0]["field_size"] == 3 and df.iloc[0]["field_size_by_year"] == 2


def test_figure_rank_is_per_figure_not_per_category():
    # (name, yob, F1 score, F2 score): figure orders are deliberately opposite.
    rows = [("A", 2016, 9.0, 1.0), ("B", 2016, 8.0, 2.0), ("C", 2015, 7.0, 3.0)]
    results = []
    for i, (nm, yob, s1, s2) in enumerate(rows):
        figs = [FigureResult("F1", [5.0] * 5, s1, 0.0), FigureResult("F2", [5.0] * 5, s2, 0.0)]
        results.append(ParsedResult(i + 1, i + 1, nm, "C", "CZE", yob, s1 + s2, 0.0, 0.0, figs))
    comp = ParsedCompetition("Cup", "2026-01-01", "", "U12", "2014–2019", 2014, 2019, 5,
                             [FigureDef("F1", "Straight Ballet Leg", None, "106"), FigureDef("F2", "Barracuda", None, "301")],
                             results)
    c = sqlite3.connect(":memory:")
    init_schema(c)
    import_competition(c, comp, sha256="fr1", filename="fr1.pdf")
    ranks = {}
    for nm, *_ in rows:
        aid = c.execute("SELECT id FROM athletes WHERE name=?", (nm,)).fetchone()[0]
        df = athlete_rankings(c, aid)
        for _, r in df.iterrows():
            assert 1 <= r["fig_rank_overall"] <= r["field_size"]
            assert 1 <= r["fig_rank_by_year"] <= r["field_size_by_year"]
            ranks[(nm, r["figure_number"])] = (int(r["fig_rank_overall"]),
                                               int(r["fig_rank_by_year"]))
    assert [ranks[(n, "F1")][0] for n in "ABC"] == [1, 2, 3]
    assert [ranks[(n, "F2")][0] for n in "ABC"] == [3, 2, 1]
    assert [ranks[(n, "F1")][1] for n in "AB"] == [1, 2]
    assert [ranks[(n, "F2")][1] for n in "AB"] == [2, 1]
    assert ranks[("C", "F1")][1] == 1 and ranks[("C", "F2")][1] == 1


def test_same_figure_name_under_different_numbers_is_one_figure():
    def comp(date, names, scores):
        res = []
        for i, (nm, sc) in enumerate(scores):
            figs = [FigureResult(f"F{k + 1}", [5.0] * 5, v, 0.0) for k, v in enumerate(sc)]
            res.append(ParsedResult(i + 1, i + 1, nm, "C", "CZE", 2016, sum(sc), 0.0, 0.0, figs))
        return ParsedCompetition(f"Cup {date}", date, "", "U12", "2014-2019", 2014, 2019, 5,
                                 [FigureDef(f"F{k + 1}", n, None, {"Straight Ballet Leg": "106", "Barracuda": "301"}[n]) for k, n in enumerate(names)],
                                 res)
    c = sqlite3.connect(":memory:")
    init_schema(c)
    # Straight Ballet Leg is F1 in cup 1 and F2 in cup 2.
    import_competition(c, comp("2026-01-01", ["Straight Ballet Leg", "Barracuda"],
                               [("X", (9.0, 1.0)), ("Y", (8.0, 2.0))]),
                       sha256="n1", filename="n1.pdf")
    import_competition(c, comp("2026-02-01", ["Barracuda", "Straight Ballet Leg"],
                               [("Y", (9.0, 9.0)), ("X", (1.0, 5.0))]),
                       sha256="n2", filename="n2.pdf")
    aid = c.execute("SELECT id FROM athletes WHERE name='X'").fetchone()[0]
    df = athlete_rankings(c, aid)
    assert sorted(df["figure_name"].unique()) == ["Barracuda", "Straight Ballet Leg"]
    ballet = df[df["figure_name"] == "Straight Ballet Leg"].sort_values("date")
    # Ranked within each competition only: X first in cup 1 (9 vs 8), second in cup 2 (5 vs 9).
    assert list(ballet["fig_rank_overall"]) == [1, 2]
    scores = athlete_figure_scores(c, aid)
    assert sorted(scores["figure_name"].unique()) == ["Barracuda", "Straight Ballet Leg"]
    assert "figure" not in scores.columns
    from ui.components import build_ranking_table
    wide, fig_cols = build_ranking_table(df, by_year=False)
    assert sorted(fig_cols) == ["Barracuda", "Straight Ballet Leg"] and len(wide) == 2


@pytest.fixture
def seeded_u12():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    comp = make(level="U12", name="Ann", club="C")
    import_competition(c, comp, sha256="u12", filename="u.pdf")
    cc_id = c.execute("SELECT id FROM competition_categories").fetchone()[0]

    class S:
        conn = c
    S.cc_id = cc_id
    S.competition_name = comp.name
    return S


def test_competition_figure_detail_has_name_and_coefficient(seeded_u12):
    df = competition_figure_detail(seeded_u12.conn, seeded_u12.cc_id)
    row = df.iloc[0]
    assert row["figure_name"] == "Straight Ballet Leg"
    assert row["coefficient"] == 1.6
    assert row["judge_1"] == 5.0 and pd.isna(row["judge_6"])


def test_athlete_figure_detail_columns(seeded_u12):
    aid = seeded_u12.conn.execute("SELECT id FROM athletes").fetchone()[0]
    df = athlete_figure_detail(seeded_u12.conn, aid)
    assert df.iloc[0]["competition"] == seeded_u12.competition_name
    assert df.iloc[0]["figure_name"] == "Straight Ballet Leg"


def test_catalogue_figures_counts_performances_and_competitions(seeded_u12):
    df = catalogue_figures(seeded_u12.conn, "U12")
    row = df[df["code"] == "106"].iloc[0]
    assert row["performances"] == 1
    assert row["competitions"] == seeded_u12.competition_name


def test_catalogue_figures_lists_unperformed_figures(seeded_u12):
    df = catalogue_figures(seeded_u12.conn, "U12")
    row = df[df["code"] == "301"].iloc[0]
    assert row["performances"] == 0


def test_figure_queries_use_catalogue_name_so_code_101_is_one_figure():
    c = sqlite3.connect(":memory:")
    init_schema(c)
    for n, (printed, date) in enumerate([("Straight Ballet Leg", "2026-01-01"),
                                         ("Ballet Leg Single", "2026-02-01")]):
        comp = make(level="L3", name="Ann", club="C")
        comp = dataclasses.replace(
            comp, date=date, figures=[FigureDef("F1", printed, None, "101")])
        import_competition(c, comp, sha256=f"n101-{n}", filename=f"n{n}.pdf")
    athlete_id = c.execute("SELECT id FROM athletes WHERE name='Ann'").fetchone()[0]
    scores = athlete_figure_scores(c, athlete_id)
    assert len(scores) == 2
    assert list(scores["figure_name"].unique()) == ["Ballet Leg Single"]
    assert set(athlete_rankings(c, athlete_id)["figure_name"]) == {"Ballet Leg Single"}
    for (rid,) in c.execute("SELECT id FROM results").fetchall():
        assert list(result_judge_marks(c, rid)["figure_name"]) == ["Ballet Leg Single"]
    for (cc,) in c.execute("SELECT id FROM competition_categories").fetchall():
        assert list(competition_figures(c, cc)["name"]) == ["Ballet Leg Single"]
