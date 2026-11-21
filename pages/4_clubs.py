import plotly.express as px
import streamlit as st

from db.database import get_connection, init_schema
from db.queries import club_avg_scores, club_list, club_medals, club_roster
from ui.components import stat_card
from ui.theme import inject_theme, plotly_layout

inject_theme()
st.title("Clubs")

conn = get_connection()
init_schema(conn)

clubs = club_list(conn)
if clubs.empty:
    st.info("No clubs yet. Use the Import page to add results.")
    conn.close()
    st.stop()

names = dict(zip(clubs["id"].astype(int), clubs["name"]))
club_id = st.selectbox("Club", list(names), format_func=names.get)

medals = club_medals(conn, int(club_id))
counts = {int(p): int(n) for p, n in zip(medals["place"], medals["count"])}
cols = st.columns(3)
for col, (place, label) in zip(cols, [(1, "Gold"), (2, "Silver"), (3, "Bronze")]):
    with col:
        stat_card(label, str(counts.get(place, 0)))

st.subheader("Roster")
st.dataframe(club_roster(conn, int(club_id)), hide_index=True, width="stretch")

avg = club_avg_scores(conn, int(club_id))
if not avg.empty:
    st.subheader("Scores")
    avg = avg.copy()
    avg["x_label"] = avg["competition"] + "<br>" + avg["date"]
    fig = px.line(avg, x="x_label", y="avg_total", markers=True,
                  title="Average score per competition",
                  labels={"avg_total": "Avg score", "x_label": ""},
                  category_orders={"x_label": list(dict.fromkeys(avg["x_label"]))})
    st.plotly_chart(plotly_layout(fig), width="stretch")
conn.close()
