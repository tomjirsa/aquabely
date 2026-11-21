import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db.database import get_connection, init_schema
from db.queries import athlete_rankings
from ui.components import build_ranking_table, stat_card, style_rank_row
from ui.theme import inject_theme, plotly_layout

inject_theme()
st.title("Athletes")

conn = get_connection()
init_schema(conn)

athletes = pd.read_sql_query(
    """SELECT a.id, a.name, a.year_of_birth, a.country, c.name AS club
       FROM athletes a JOIN clubs c ON c.id = a.club_id ORDER BY a.name""", conn)
if athletes.empty:
    st.info("No athletes yet. Use the Import page to add results.")
    conn.close()
    st.stop()

query = st.text_input("Search by name").strip().lower()
found = athletes
if query:
    found = athletes[athletes["name"].str.lower().str.contains(query, regex=False)]
if found.empty:
    st.warning("No athlete matches that search.")
    conn.close()
    st.stop()

labels = {int(i): f"{n} ({c})" for i, n, c in zip(found["id"], found["name"], found["club"])}
athlete_id = st.selectbox("Athlete", list(labels), format_func=labels.get)
a = athletes[athletes["id"] == athlete_id].iloc[0]

c1, c2, c3 = st.columns(3)
with c1:
    stat_card("Name", str(a["name"]))
with c2:
    stat_card("Club", str(a["club"]))
with c3:
    yob = a["year_of_birth"]
    stat_card("Born", "n/a" if pd.isna(yob) else str(int(yob)))

st.subheader("History")
history = pd.read_sql_query(
    """SELECT cat.code AS level, c.name AS competition, c.date AS date,
              cc.age_group_label AS age_group, r.rank AS rank,
              r.total_score AS total_score
       FROM results r
       JOIN competition_categories cc ON cc.id = r.competition_category_id
       JOIN competitions c ON c.id = cc.competition_id
       JOIN categories cat ON cat.id = cc.category_id
       WHERE r.athlete_id = ? ORDER BY c.date""", conn, params=(int(athlete_id),))
st.dataframe(history, hide_index=True, width="stretch")

rank_df = athlete_rankings(conn, int(athlete_id))
if rank_df.empty:
    st.caption("No figure rankings available for this athlete.")
else:
    by_year = st.toggle("Rank within birth year", value=False)
    wide, fig_cols = build_ranking_table(rank_df, by_year)
    st.subheader("Figure ranks")
    st.dataframe(wide.style.apply(style_rank_row, fig_cols=fig_cols, axis=1),
                 hide_index=True, width="stretch")

    st.subheader("Rank over time")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=wide["date"], y=wide["overall_rank"],
                             mode="lines+markers", name="Overall"))
    for col in fig_cols:
        fig.add_trace(go.Scatter(x=wide["date"], y=wide[col], mode="lines+markers",
                                 name=col, visible="legendonly"))
    fig.update_yaxes(autorange="reversed", title="Rank")
    st.plotly_chart(plotly_layout(fig), width="stretch")
conn.close()
