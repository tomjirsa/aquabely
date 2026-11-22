import streamlit as st

from db.database import get_connection, init_schema
from db.queries import (competition_figure_detail, competition_figures,
                        competition_judge_detail,
                        competitions_for_level, results_for)
from ui.components import judge_marks_table, render_column_filters
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
    with st.expander("Filter results", expanded=True):
        shown = render_column_filters(results, key=f"results_{cc_id}")
    st.caption(f"Showing {len(shown)} of {len(results)} results")
    st.dataframe(shown, hide_index=True, width="stretch")

figures = competition_figures(conn, cc_id)
if not figures.empty:
    st.subheader("Figures")
    if figures["difficulty"].isna().all():
        figures = figures.drop(columns=["difficulty"])
    st.dataframe(figures, hide_index=True)

    with st.expander("Judge detail"):
        detail = competition_judge_detail(conn, cc_id)
        st.markdown(judge_marks_table(detail))

    with st.expander("Figure detail"):
        fdetail = competition_figure_detail(conn, cc_id)
        st.markdown(judge_marks_table(fdetail))
conn.close()
