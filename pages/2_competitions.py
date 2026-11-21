import pandas as pd
import streamlit as st

from db.database import get_connection, init_schema
from db.queries import competitions_for_level, results_for
from ui.theme import inject_theme

inject_theme()
st.title("Competitions")

conn = get_connection()
init_schema(conn)

level = st.radio("Level", ["L3", "U12"], horizontal=True)
comps = competitions_for_level(conn, level)

if comps.empty:
    st.info(f"No {level} competitions yet. Use the Import page to add one.")
    conn.close()
    st.stop()

names = list(dict.fromkeys(comps["competition"]))
competition = st.selectbox("Competition", names)
groups = comps[comps["competition"] == competition]
label = st.selectbox("Age group", list(groups["age_group_label"]))
cc_id = int(groups[groups["age_group_label"] == label].iloc[0]["competition_category_id"])

results = results_for(conn, cc_id)
if results.empty:
    st.info("No results for this age group.")
else:
    st.dataframe(results, hide_index=True, width="stretch")

figures = pd.read_sql_query(
    "SELECT number, name, difficulty FROM figures WHERE competition_category_id = ? ORDER BY id",
    conn, params=(cc_id,))
if not figures.empty:
    st.subheader("Figures")
    if figures["difficulty"].isna().all():
        figures = figures.drop(columns=["difficulty"])
    st.dataframe(figures, hide_index=True)

    with st.expander("Judge detail"):
        detail = pd.read_sql_query(
            """SELECT a.name AS athlete, f.number AS figure, fr.score AS score,
                      fr.penalty AS penalty, fr.judge_1, fr.judge_2, fr.judge_3,
                      fr.judge_4, fr.judge_5, fr.judge_6, fr.judge_7
               FROM figure_results fr
               JOIN results r ON r.id = fr.result_id
               JOIN athletes a ON a.id = r.athlete_id
               JOIN figures f ON f.id = fr.figure_id
               WHERE r.competition_category_id = ?
               ORDER BY r.rank, a.name, f.id""", conn, params=(cc_id,))
        empty = [c for c in detail.columns if c.startswith("judge_") and detail[c].isna().all()]
        st.dataframe(detail.drop(columns=empty), hide_index=True, width="stretch")
conn.close()
