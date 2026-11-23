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
