"""Create a seeded temporary SQLite database for the Playwright smoke tests.

Usage: python scripts/seed_e2e.py [path]
Prints the database path. Without an argument a fresh temp file is created.
Never touches the user's real database or data/.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> str:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        fd, name = tempfile.mkstemp(prefix="aquabely_e2e_", suffix=".db")
        os.close(fd)
        path = Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    os.environ["AQUABELY_DB"] = str(path)

    from db.database import get_connection, init_schema
    from db.importer import import_competition
    from tests.test_importer import make

    import db.database
    db.database.DB_PATH = path
    conn = get_connection()
    init_schema(conn)
    import_competition(conn, make(level="L3", name="Bea", club="Club L"),
                       sha256="e2e-l3", filename="l3.pdf")
    import_competition(conn, make(level="U12", name="Ann", club="Club U"),
                       sha256="e2e-u12", filename="u12.pdf")
    conn.close()
    print(path)
    return str(path)


if __name__ == "__main__":
    main()
