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
