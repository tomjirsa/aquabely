import pytest

from db.database import get_connection, init_schema
from db.importer import import_competition


@pytest.fixture
def seeded_app_db(tmp_path, monkeypatch):
    """Point AQUABELY_DB at a temp file seeded with one U12 competition."""
    from tests.test_importer import make
    path = tmp_path / "seeded.db"
    monkeypatch.setenv("AQUABELY_DB", str(path))
    import db.database
    # DB_PATH is read at import time; patch it so the pages use the temp file.
    monkeypatch.setattr(db.database, "DB_PATH", path)
    conn = get_connection()
    init_schema(conn)
    import_competition(conn, make(level="U12", name="Ann", club="C"),
                       sha256="u12", filename="u.pdf")
    conn.close()
    return path
