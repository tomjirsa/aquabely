"""Ranking and result queries against the U12-refactor schema."""
import pandas as pd

_RANKINGS_SQL = """
WITH all_ranks AS (
    SELECT
        r.id AS result_id,
        r.athlete_id,
        c.name AS competition,
        c.date,
        RANK() OVER (PARTITION BY r.competition_category_id
                     ORDER BY r.total_score DESC) AS rank_overall,
        RANK() OVER (PARTITION BY r.competition_category_id, a.year_of_birth
                     ORDER BY r.total_score DESC) AS rank_by_year
    FROM results r
    JOIN athletes a ON a.id = r.athlete_id
    JOIN competition_categories cc ON cc.id = r.competition_category_id
    JOIN competitions c ON c.id = cc.competition_id
),
fig_ranks AS (
    SELECT
        fr.result_id,
        f.number AS figure_number,
        RANK() OVER (PARTITION BY f.competition_category_id
                     ORDER BY fr.score DESC) AS fig_rank_overall,
        RANK() OVER (PARTITION BY f.competition_category_id, a.year_of_birth
                     ORDER BY fr.score DESC) AS fig_rank_by_year
    FROM figure_results fr
    JOIN figures f ON f.id = fr.figure_id
    JOIN results r ON r.id = fr.result_id
    JOIN athletes a ON a.id = r.athlete_id
)
SELECT
    ar.competition, ar.date, ar.rank_overall, ar.rank_by_year,
    fr.figure_number, fr.fig_rank_overall, fr.fig_rank_by_year
FROM all_ranks ar
JOIN fig_ranks fr ON fr.result_id = ar.result_id
WHERE ar.athlete_id = ?
ORDER BY ar.date, fr.figure_number
"""


def competitions_for_level(conn, level_code):
    return pd.read_sql_query(
        """SELECT cc.id AS competition_category_id, c.name AS competition,
                  c.date AS date, cc.age_group_label AS age_group_label
           FROM competition_categories cc
           JOIN competitions c ON c.id = cc.competition_id
           JOIN categories cat ON cat.id = cc.category_id
           WHERE cat.code = ?
           ORDER BY c.date, cc.id""",
        conn, params=(level_code,))


def results_for(conn, competition_category_id):
    return pd.read_sql_query(
        """SELECT r.rank AS rank, a.name AS name, cl.name AS club,
                  a.country AS country, r.total_score AS total_score,
                  r.penalty AS penalty, r.points_behind AS points_behind
           FROM results r
           JOIN athletes a ON a.id = r.athlete_id
           JOIN clubs cl ON cl.id = r.club_id
           WHERE r.competition_category_id = ?
           ORDER BY r.rank, a.name""",
        conn, params=(competition_category_id,))


def athlete_rankings(conn, athlete_id):
    return pd.read_sql_query(_RANKINGS_SQL, conn, params=(athlete_id,))


def club_medals(conn, club_id):
    return pd.read_sql_query(
        """SELECT rank AS place, COUNT(*) AS count
           FROM results
           WHERE club_id = ? AND rank IN (1, 2, 3)
           GROUP BY rank ORDER BY rank""",
        conn, params=(club_id,))


def athlete_list(conn):
    return pd.read_sql_query(
        """SELECT a.id AS id, a.name AS name, cl.name AS club,
                  a.country AS country, a.year_of_birth AS year_of_birth
           FROM athletes a JOIN clubs cl ON cl.id = a.club_id
           ORDER BY a.name, a.id""", conn)


def athlete_history(conn, athlete_id):
    return pd.read_sql_query(
        """SELECT r.id AS result_id, r.competition_category_id AS competition_category_id,
                  cat.code AS level, c.name AS competition, c.date AS date,
                  cc.age_group_label AS age_group, r.rank AS rank,
                  r.total_score AS total_score
           FROM results r
           JOIN competition_categories cc ON cc.id = r.competition_category_id
           JOIN competitions c ON c.id = cc.competition_id
           JOIN categories cat ON cat.id = cc.category_id
           WHERE r.athlete_id = ?
           ORDER BY c.date, r.id""",
        conn, params=(athlete_id,))


def athlete_overall_ranks(conn, athlete_id):
    """Overall/by-year ranks per result; works without figure results."""
    return pd.read_sql_query(
        """SELECT competition, date, rank_overall, rank_by_year FROM (
               SELECT r.athlete_id AS athlete_id, c.name AS competition, c.date AS date,
                      RANK() OVER (PARTITION BY r.competition_category_id
                                   ORDER BY r.total_score DESC) AS rank_overall,
                      RANK() OVER (PARTITION BY r.competition_category_id, a.year_of_birth
                                   ORDER BY r.total_score DESC) AS rank_by_year
               FROM results r
               JOIN athletes a ON a.id = r.athlete_id
               JOIN competition_categories cc ON cc.id = r.competition_category_id
               JOIN competitions c ON c.id = cc.competition_id)
           WHERE athlete_id = ? ORDER BY date""",
        conn, params=(athlete_id,))


def athlete_figure_scores(conn, athlete_id):
    return pd.read_sql_query(
        """SELECT c.date AS date, c.name AS competition, f.number AS figure,
                  f.name AS figure_name, fr.score AS figure_score
           FROM figure_results fr
           JOIN results r ON r.id = fr.result_id
           JOIN figures f ON f.id = fr.figure_id
           JOIN competition_categories cc ON cc.id = r.competition_category_id
           JOIN competitions c ON c.id = cc.competition_id
           WHERE r.athlete_id = ?
           ORDER BY c.date, f.id""",
        conn, params=(athlete_id,))


def result_judge_marks(conn, result_id):
    return pd.read_sql_query(
        """SELECT f.number AS figure, f.name AS figure_name,
                  fr.judge_1, fr.judge_2, fr.judge_3, fr.judge_4,
                  fr.judge_5, fr.judge_6, fr.judge_7
           FROM figure_results fr
           JOIN figures f ON f.id = fr.figure_id
           WHERE fr.result_id = ?
           ORDER BY f.id""",
        conn, params=(result_id,))


def level_athlete_count(conn, level_code):
    row = conn.execute(
        """SELECT COUNT(DISTINCT r.athlete_id)
           FROM results r
           JOIN competition_categories cc ON cc.id = r.competition_category_id
           JOIN categories cat ON cat.id = cc.category_id
           WHERE cat.code = ?""", (level_code,)).fetchone()
    return int(row[0])


def club_list(conn):
    return pd.read_sql_query("SELECT id, name FROM clubs ORDER BY name", conn)


def club_roster(conn, club_id):
    return pd.read_sql_query(
        """SELECT a.name AS name, a.year_of_birth AS year_of_birth, a.country AS country
           FROM athletes a
           WHERE a.id IN (SELECT athlete_id FROM results WHERE club_id = ?)
           ORDER BY a.name""",
        conn, params=(club_id,))


def club_avg_scores(conn, club_id):
    return pd.read_sql_query(
        """SELECT c.name AS competition, c.date AS date,
                  AVG(r.total_score) AS avg_total
           FROM results r
           JOIN competition_categories cc ON cc.id = r.competition_category_id
           JOIN competitions c ON c.id = cc.competition_id
           WHERE r.club_id = ?
           GROUP BY c.id, c.name, c.date
           ORDER BY c.date, c.id""",
        conn, params=(club_id,))


def competition_figures(conn, competition_category_id):
    return pd.read_sql_query(
        """SELECT number, name, difficulty FROM figures
           WHERE competition_category_id = ? ORDER BY id""",
        conn, params=(competition_category_id,))


def competition_judge_detail(conn, competition_category_id):
    return pd.read_sql_query(
        """SELECT a.name AS athlete, f.number AS figure, fr.score AS score,
                  fr.penalty AS penalty, fr.judge_1, fr.judge_2, fr.judge_3,
                  fr.judge_4, fr.judge_5, fr.judge_6, fr.judge_7
           FROM figure_results fr
           JOIN results r ON r.id = fr.result_id
           JOIN athletes a ON a.id = r.athlete_id
           JOIN figures f ON f.id = fr.figure_id
           WHERE r.competition_category_id = ?
           ORDER BY r.rank, a.name, f.id""",
        conn, params=(competition_category_id,))
