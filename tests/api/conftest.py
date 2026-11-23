import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AQUABELY_DB", str(tmp_path / "api.db"))
    import db.database
    monkeypatch.setattr(db.database, "DB_PATH", tmp_path / "api.db")
    from api.main import app
    return TestClient(app)


@pytest.fixture
def seeded_client(seeded_app_db):
    from api.main import app
    return TestClient(app)


@pytest.fixture
def seeded_cc_id(seeded_app_db):
    from db.database import get_connection
    conn = get_connection()
    try:
        return conn.execute("SELECT id FROM competition_categories ORDER BY id").fetchone()[0]
    finally:
        conn.close()


@pytest.fixture
def athlete_without_figures_id(tmp_path, monkeypatch):
    """One competition with one result and no figure_results rows; returns the athlete id."""
    from db.database import get_connection, init_schema
    from db.importer import import_competition
    from tests.test_importer import make
    path = tmp_path / "nofig.db"
    monkeypatch.setenv("AQUABELY_DB", str(path))
    import db.database
    monkeypatch.setattr(db.database, "DB_PATH", path)
    comp = make(level="U12", name="Nofig", club="C")
    import dataclasses
    comp = dataclasses.replace(comp, figures=[], results=[dataclasses.replace(comp.results[0], figure_results=[])])
    conn = get_connection()
    try:
        init_schema(conn)
        import_competition(conn, comp, sha256="nofig", filename="n.pdf")
        assert conn.execute("SELECT COUNT(*) FROM figure_results").fetchone()[0] == 0
        return conn.execute("SELECT id FROM athletes WHERE name='Nofig'").fetchone()[0]
    finally:
        conn.close()
