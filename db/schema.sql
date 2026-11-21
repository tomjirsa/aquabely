CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    source_sha256 TEXT NOT NULL UNIQUE,
    imported_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS competition_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL REFERENCES competitions(id),
    category_id INTEGER NOT NULL REFERENCES categories(id),
    age_group_label TEXT NOT NULL,
    birth_year_from INTEGER,
    birth_year_to INTEGER,
    judges_per_figure INTEGER NOT NULL,
    UNIQUE(competition_id, category_id, age_group_label)
);

CREATE TABLE IF NOT EXISTS figures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_category_id INTEGER NOT NULL REFERENCES competition_categories(id),
    number TEXT NOT NULL,
    name TEXT NOT NULL,
    difficulty REAL
);

CREATE TABLE IF NOT EXISTS athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT,
    year_of_birth INTEGER,
    club_id INTEGER NOT NULL REFERENCES clubs(id),
    UNIQUE(name, club_id)
);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_category_id INTEGER NOT NULL REFERENCES competition_categories(id),
    athlete_id INTEGER NOT NULL REFERENCES athletes(id),
    club_id INTEGER NOT NULL REFERENCES clubs(id),
    entry_number INTEGER,
    rank INTEGER,
    total_score REAL,
    penalty REAL,
    points_behind REAL,
    UNIQUE(competition_category_id, athlete_id)
);

CREATE TABLE IF NOT EXISTS figure_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL REFERENCES results(id),
    figure_id INTEGER NOT NULL REFERENCES figures(id),
    score REAL,
    penalty REAL,
    judge_1 REAL,
    judge_2 REAL,
    judge_3 REAL,
    judge_4 REAL,
    judge_5 REAL,
    judge_6 REAL,
    judge_7 REAL
);

CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    status TEXT NOT NULL,
    error TEXT,
    imported_at TEXT NOT NULL
);
