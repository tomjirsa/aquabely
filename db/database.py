import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("AQUABELY_DB", Path.home() / "aquabely.db"))
_SCHEMA = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(categories)")]
    if cols and "code" not in cols:
        raise RuntimeError(
            "Database uses the old schema. Delete or rename the database file "
            "(see docs/deployment.md) and restart.")
    conn.executescript(_SCHEMA.read_text(encoding="utf-8"))
