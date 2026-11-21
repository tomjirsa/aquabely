import sqlite3
from db.database import init_schema
from parser.catalogue import CATALOGUE


def test_catalogue_has_l3_and_u12_entries():
    levels = {e.level for e in CATALOGUE}
    assert levels == {"L3", "U12"}
    l3 = {e.code: e.coefficient for e in CATALOGUE if e.level == "L3" and e.code}
    assert l3 == {"101": 1.6, "316": 1.4}
    u12 = {e.code: e.coefficient for e in CATALOGUE if e.level == "U12"}
    assert u12["106"] == 1.6 and u12["301"] == 1.8 and u12["359"] == 2.2 and u12["348"] == 1.9


def test_seed_is_idempotent():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    init_schema(conn)
    assert conn.execute("SELECT COUNT(*) FROM figure_catalogue").fetchone()[0] == len(CATALOGUE)


def test_seeded_rows_equal_catalogue():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    rows = conn.execute(
        "SELECT code, level, name, coefficient, description_cs FROM figure_catalogue").fetchall()
    key = lambda t: (t[0] or "", t[1], t[2])
    expected = [(e.code, e.level, e.name, e.coefficient, e.description_cs) for e in CATALOGUE]
    assert sorted(rows, key=key) == sorted(expected, key=key)
