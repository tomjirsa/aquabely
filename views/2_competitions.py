import streamlit as st

from db.database import get_connection, init_schema
from db.queries import competition_figure_detail, competitions_for_level, results_for
from ui.components import (JUDGE_COLS, figure_detail_html, filter_results, results_table_html)
from ui.theme import inject_theme

FILTER_FIELDS = ["name", "born", "club", "country", "score", "penalty", "behind"]
FILTER_PLACEHOLDERS = {"name": "Filter", "born": "Year", "club": "Filter", "country": "Filter",
                       "score": "Min - max", "penalty": "Min - max", "behind": "Min - max"}
COLUMN_WIDTHS = [1, 3, 1.2, 3, 1.6, 1.4, 1.4, 1.4]  # rank, then one slot per filter

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
competition = st.selectbox("Competition", names, index=None, placeholder="Select a competition")
if competition is None:
    conn.close()
    st.stop()

cc_id = int(comps[comps["competition"] == competition].iloc[0]["competition_category_id"])
results = results_for(conn, cc_id)
if results.empty:
    st.info("No results for this competition.")
    conn.close()
    st.stop()

st.subheader("Results")
slots = st.columns(COLUMN_WIDTHS)
filters = {}
for slot, field in zip(slots[1:], FILTER_FIELDS):
    with slot:
        filters[field] = st.text_input(f"Filter {field}", key=f"flt_{cc_id}_{field}",
                                       placeholder=FILTER_PLACEHOLDERS[field],
                                       label_visibility="collapsed")
active = any(value.strip() for value in filters.values())
shown = filter_results(results, filters)
st.caption(f"Showing {len(shown)} of {len(results)} results")
if shown.empty:
    st.info("No results match these filters.")
else:
    st.markdown(results_table_html(shown, active), unsafe_allow_html=True)

st.subheader("Figure detail")
detail = competition_figure_detail(conn, cc_id)
groups = [(name, detail[detail["athlete"] == name]) for name in dict.fromkeys(shown["name"])]
groups = [(name, figs) for name, figs in groups if not figs.empty]
if not groups:
    st.caption("No figure results for these athletes.")
else:
    judge_cols = [c for c in JUDGE_COLS if detail[c].notna().any()]
    st.markdown(figure_detail_html(groups, judge_cols), unsafe_allow_html=True)
conn.close()
