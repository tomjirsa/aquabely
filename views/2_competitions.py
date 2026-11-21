import streamlit as st

from db.database import get_connection, init_schema
from db.queries import (competition_figure_detail, competition_figures,
                        competition_judge_detail,
                        competitions_for_level, results_for)
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

figures = competition_figures(conn, cc_id)
if not figures.empty:
    st.subheader("Figures")
    if figures["difficulty"].isna().all():
        figures = figures.drop(columns=["difficulty"])
    st.dataframe(figures, hide_index=True)

    with st.expander("Judge detail"):
        detail = competition_judge_detail(conn, cc_id)
        empty = [c for c in detail.columns if c.startswith("judge_") and detail[c].isna().all()]
        st.dataframe(detail.drop(columns=empty), hide_index=True, width="stretch")

    with st.expander("Figure detail"):
        fdetail = competition_figure_detail(conn, cc_id)
        empty = [c for c in fdetail.columns if c.startswith("judge_") and fdetail[c].isna().all()]
        st.dataframe(fdetail.drop(columns=empty), hide_index=True, width="stretch")
conn.close()
