CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);

INSERT OR IGNORE INTO categories(code, name) VALUES ('L3', 'Level 3'), ('U12', 'Under 12');

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
    difficulty REAL,
    catalogue_id INTEGER REFERENCES figure_catalogue(id)
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

CREATE TABLE IF NOT EXISTS figure_catalogue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,
    level TEXT NOT NULL,
    name TEXT NOT NULL,
    coefficient REAL NOT NULL,
    description_cs TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL,
    UNIQUE(level, code, name)
);

-- SQLite treats NULLs as distinct in UNIQUE constraints, so figures without a
-- code need this index to keep the seed idempotent.
CREATE UNIQUE INDEX IF NOT EXISTS idx_figure_catalogue_identity
    ON figure_catalogue(level, COALESCE(code, ''), name);

INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES ('101', 'L3', 'Ballet Leg Single', 1.6, 'Figura začíná v poloze na znaku (Back Layout Position). Jedna noha zůstává stále natažená na hladině a druhá noha je skrčována podél vnitřní strany natažené nohy do Bent Knee Back Layout Position. Pokrčená noha je bez pohybu stehna natažena do Ballet Leg Position. Z polohy Ballet Leg Position je přednožená noha bez pohybu stehna skrčována do Bent Knee Back Layout Position. Skrčená noha je natažena (palec skrčené nohy je veden po vnitřní straně natažené nohy). Figura končí v poloze na znaku (Back Layout Position).', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES (NULL, 'L3', 'From Back Layout Position to Surface Arch Position to Back Layout Position', 1.2, 'Z polohy na znaku (Back Layout Position) je proveden postupný zájezd směrem za hlavou pod hladinu - hlava, kyčle i nohy se posouvají po hladině. Při postupném zájezdu pod hladinu se nejdříve zanoří hlava a zároveň se záda prohýbají do polohy Surface Arch Position, kdy kyčle na hladině nahradí původní pozici hlavy. V pozici Surface Arch Position je provedena výdrž. Následuje výjezd na hladině směrem za nohami, kdy postupně vyjíždí na hladinu kyčle, hrudník a hlava, kdy hlava současně nahradí pozici kyčlí. Figura končí v poloze na znaku (Back Layout Position).', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES ('316', 'L3', 'Kipnus', 1.4, 'Z polohy na znaku jsou kolena, holeně a špičky vedeny po hladině do Tuck Position. Plynule je tuck kompaktnější a následuje částečné salto skrčmo vzad až do okamžiku, kdy jsou holeně kolmé na hladinu. Rozbalováním trupu a natahováním nohou je zaujata Bent Knee Vertical Position uprostřed svislé osy mezi místem, kde původně byly kyčle a holeně. Figura pokračuje kontrolovaným vertikálním zájezdem (Vertical Descent) v pozici Bent Knee Vertical Position až pod hladinu.', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES (NULL, 'L3', 'Walkover Front Variant', 1.3, 'Figura začíná v poloze na břiše (Front Layout Position). Z polohy Front Layout Position je proveden zájezd do polohy Front Pike Position, při zájezdu kyčle nahradí pozici hlavy a hlava se dostane do jedné linie s hýžděmi. Jedna noha se kontrolovaně pohybuje ve vertikálním oblouku o 180° nad hladinou až do polohy Split Position. Figura končí dosažením polohy Surface Split Position. Výjezd z finální polohy (Surface Split Position) je ponechán na volbě soutěžícího, doporučuje se však, aby soutěžící provedl snožení nohou do pozice Tuck Position a provedl rotaci 180° (v libovolném směru) s následným výjezdem na hladinu.', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES ('106', 'U12', 'Straight Ballet Leg', 1.6, 'Figura začíná v poloze na znaku. Jedna natažená noha je zvedána do Ballet Leg Position, následuje přechod Lower a Ballet Leg a figura končí v poloze na znaku.', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES ('301', 'U12', 'Barracuda', 1.8, 'Z polohy na znaku jsou nohy přednožovány do svislé osy a trup je ponořován do Back Pike Position tak, že špičky jsou těsně pod hladinou. Rychlým svislým pohybem Thrust – vyražení je zaujata Vertical Position. Figura končí svislým klesáním těla pod hladinu, které má stejné tempo jako vyražení.', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES ('359', 'U12', 'Front Ariana', 2.2, 'Z polohy na prsou je proveden přechod Front Pike Position. Jedna noha je zvedána 180° obloukem nad hladinou až do Split Position. Nohy zůstávají ležet na hladině a tělo se protočí v kyčlích o 180° – Ariana Rotation. Figura končí přechodem Walkout Front v poloze na znaku.', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES ('348', 'U12', 'Tower', 1.9, 'Z polohy na prsou je proveden přechod Front Pike Position. Jedna noha je zvedána do Fishtail Position. Přednožená noha je přinožena do Vertical Position. Figura končí svislým klesáním těla pod hladinu.', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES ('363', 'U12', 'Water Drop', 1.8, 'Z polohy na prsou je proveden přechod Front Pike Position. Nohy jsou zvedány nad hladinu se současným pokrčováním jedné nohy až do Bent Knee Vertical Position. Je proveden Twist o 180°. Následuje Spin o 180° ve stejném směru otáčení se současným přinožením skrčené nohy do Verical Position. Přinožení musí být dokončeno v okamžiku, kdy kotníky protnou hladinu. Figura končí svislým klesáním těla pod hladinu.', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES ('401', 'U12', 'Swordfish', 2.1, 'V poloze na prsou je zaujata Bent Knee Position. Prohnutím a přetáčením těla vzad kolem osy boků je napjatá noha vedena 180° obloukem nad hladinou do Bent Knee Surface Arch Position. Skrčená noha je přinožena a přechodem Arch to Back Layout Finish Action figura končí v poloze na znaku.', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES ('311', 'U12', 'Kip', 1.6, 'Z polohy na znaku jsou kolena, holeně a špičky vedeny po hladině do Tuck Position. Plynule je tuck kompaktnější a následuje částečné salto skrčmo vzad až do okamžiku, kdy jsou holeně kolmé na hladinu. Rozbalováním trupu a natahováním nohou je zaujata Vertical Position uprostřed svislé osy mezi místem, kde původně byly kyčle a holeně. Figura končí svislým klesáním těla pod hladinu.', 'SY_STD_2026');
INSERT OR IGNORE INTO figure_catalogue(code, level, name, coefficient, description_cs, source) VALUES ('227d', 'U12', 'Swanita Spinning 180°', 1.9, 'Z polohy na znaku je proveden přechod Bent knee Surface Arch Position do Bent Knee Surface Arch Position. Skrčená noha je natažena do Knight Position. Tělo provede obrat o 180° do Fishtail Position. Ve stejném směru otáčení následuje klesající Spinning o 180° a současně je přednožená noha přinožována do Vertical Position. Snožení ve svislé poloze musí být dokončeno v okamžiku, kdy kotníky protnou hladinu. Figura končí svislým klesáním těla pod hladinu.', 'SY_STD_2026');
