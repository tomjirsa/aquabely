CREATE TABLE IF NOT EXISTS competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    location TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL REFERENCES competitions(id),
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS figures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    number TEXT NOT NULL,
    name TEXT NOT NULL,
    difficulty REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    club TEXT NOT NULL,
    year_of_birth INTEGER,
    UNIQUE(name, club)
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_id INTEGER NOT NULL REFERENCES athletes(id),
    category_id INTEGER NOT NULL REFERENCES categories(id),
    entry_number INTEGER,
    rank INTEGER NOT NULL,
    total_score REAL NOT NULL,
    penalty REAL NOT NULL DEFAULT 0.0,
    points_behind REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS figure_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL REFERENCES results(id),
    figure_id INTEGER NOT NULL REFERENCES figures(id),
    score REAL NOT NULL,
    penalty REAL NOT NULL DEFAULT 0.0,
    judge_1 REAL, judge_2 REAL, judge_3 REAL, judge_4 REAL,
    judge_5 REAL, judge_6 REAL, judge_7 REAL
);

CREATE TABLE IF NOT EXISTS imported_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    UNIQUE(sha256)
);
