import pandas as pd
import streamlit as st

from db.database import get_connection, init_schema
from db.queries import club_medals
from ui.components import stat_card
from ui.theme import inject_theme

inject_theme()
st.title("Clubs")

conn = get_connection()
init_schema(conn)

clubs = pd.read_sql_query("SELECT id, name FROM clubs ORDER BY name", conn)
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
roster = pd.read_sql_query(
    "SELECT name, year_of_birth, country FROM athletes WHERE club_id = ? ORDER BY name",
    conn, params=(int(club_id),))
st.dataframe(roster, hide_index=True, width="stretch")
conn.close()
