import dataclasses
import sqlite3
import pytest
from db.database import init_schema
from db.importer import import_competition, DuplicateImportError, ValidationFailed
from parser.models import FigureDef, FigureResult, ParsedCompetition, ParsedResult


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    init_schema(c)
    c.commit()  # seed data must survive the importer's rollback
    yield c


def make(level="L3", name="A", club="C", judges=5):
    fr = FigureResult("F1", [5.0] * judges, 5.0, 0.0)
    r = ParsedResult(1, 1, name, club, "CZE", 2016, 50.0, 0.0, 0.0, [fr])
    return ParsedCompetition("Cup", "2026-01-01", "", level, "2014–2019", 2014, 2019,
                             judges, [FigureDef("F1", "Straight Ballet Leg", None, "106")], [r])


def test_import_writes_rows(conn):
    cid = import_competition(conn, make(), sha256="h1", filename="a.pdf")
    assert conn.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 1
    assert cid == 1


def test_reimport_same_hash_is_refused_and_writes_nothing(conn):
    import_competition(conn, make(), sha256="h1", filename="a.pdf")
    with pytest.raises(DuplicateImportError):
        import_competition(conn, make(), sha256="h1", filename="a.pdf")
    assert conn.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 1


def test_validation_error_writes_no_data_and_logs_rejection(conn):
    bad = make(judges=5)
    bad.results[0].figure_results[0].judge_scores.pop()
    with pytest.raises(ValidationFailed):
        import_competition(conn, bad, sha256="h2", filename="b.pdf")
    assert conn.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM imports").fetchone()[0] == 1
    assert conn.execute("SELECT status FROM imports").fetchone()[0] == "rejected"


def test_mid_write_failure_rolls_back_everything_and_logs_rejection(conn):
    comp = make()
    dup = ParsedResult(2, 2, "A", "C", "CZE", 2016, 49.0, 0.0, 1.0,
                       [FigureResult("F1", [5.0] * 5, 5.0, 0.0)])
    comp.results.append(dup)  # same athlete+club -> UNIQUE(competition_category_id, athlete_id)
    with pytest.raises(sqlite3.IntegrityError):
        import_competition(conn, comp, sha256="h6", filename="dup.pdf")
    for table in ("clubs", "athletes", "competitions", "competition_categories",
                  "figures", "results", "figure_results"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0, table
    rows = conn.execute("SELECT status FROM imports").fetchall()
    assert rows == [("rejected",)]


def test_same_athlete_in_two_levels_is_one_row(conn):
    import_competition(conn, make(level="L3", name="Shared", club="C"), sha256="h3", filename="l3.pdf")
    import_competition(conn, make(level="U12", name="Shared", club="C", judges=5), sha256="h4", filename="u12.pdf")
    assert conn.execute("SELECT COUNT(*) FROM athletes WHERE name='Shared'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 2


def test_nonzero_penalty_round_trips(conn):
    fr = FigureResult("F1", [5.0] * 5, 5.0, 0.5)
    r = ParsedResult(1, 1, "A", "C", "CZE", 2016, 50.0, 1.5, 0.0, [fr])
    comp = ParsedCompetition("Cup", "2026-01-01", "", "L3", "2014–2019", 2014, 2019,
                             5, [FigureDef("F1", "Straight Ballet Leg", None, "106")], [r])
    import_competition(conn, comp, sha256="h5", filename="p.pdf")
    assert conn.execute("SELECT penalty FROM results").fetchone()[0] == 1.5
    assert conn.execute("SELECT penalty FROM figure_results").fetchone()[0] == 0.5
    assert conn.execute("SELECT total_score FROM results").fetchone()[0] == 50.0


def _comp_with_figure(level, code, name, sha_unused=None):
    return dataclasses.replace(make(level=level), figures=[FigureDef("F1", name, None, code)])


def _u12_comp_with_figure(code, name):
    return _comp_with_figure("U12", code, name)


def _l3_comp_with_figure(name, code=None):
    return _comp_with_figure("L3", code, name)


def test_import_links_figures_to_catalogue_and_stores_coefficient(conn):
    comp = _u12_comp_with_figure(code="106", name="Straight Ballet Leg")
    import_competition(conn, comp, sha256="cat1", filename="u12.pdf")
    row = conn.execute("SELECT f.difficulty, c.code FROM figures f JOIN figure_catalogue c ON c.id = f.catalogue_id").fetchone()
    assert row == (1.6, "106")


def test_codeless_l3_figure_links_to_catalogue(conn):
    comp = _l3_comp_with_figure(name="Walkover Front Variant")
    import_competition(conn, comp, sha256="cat3", filename="l3.pdf")
    row = conn.execute("SELECT f.difficulty, c.name FROM figures f JOIN figure_catalogue c ON c.id = f.catalogue_id").fetchone()
    assert row == (1.3, "Walkover Front Variant")


def test_unmatched_figure_rejects_import_and_writes_nothing(conn):
    comp = _l3_comp_with_figure(name="Mystery Spin")
    with pytest.raises(ValidationFailed):
        import_competition(conn, comp, sha256="cat2", filename="bad.pdf")
    assert conn.execute("SELECT COUNT(*) FROM figures").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM competitions").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM imports").fetchone()[0] == 1
    assert conn.execute("SELECT status FROM imports").fetchone()[0] == "rejected"
