import pandas as pd
import streamlit as st

import db.database as database

st.title("Competitions")

database.init_schema()

with database.get_connection() as conn:
    comps = pd.read_sql(
        "SELECT id, name, date FROM competitions ORDER BY date DESC", conn
    )

if comps.empty:
    st.info("No data yet — import PDFs on the Import page.")
    st.stop()

comp_label = st.selectbox(
    "Competition",
    comps.apply(lambda r: f"{r['name']} ({r['date']})", axis=1).tolist(),
)
comp_id = int(comps.iloc[
    comps.apply(lambda r: f"{r['name']} ({r['date']})", axis=1).tolist().index(comp_label)
]["id"])

with database.get_connection() as conn:
    cats = pd.read_sql(
        "SELECT id, name FROM categories WHERE competition_id = ?",
        conn, params=(comp_id,),
    )

if cats.empty:
    st.info("No categories found.")
    st.stop()

cat_name = st.selectbox("Category", cats["name"].tolist())
cat_id = int(cats[cats["name"] == cat_name].iloc[0]["id"])

with database.get_connection() as conn:
    df = pd.read_sql(
        """
        SELECT r.rank, a.name, a.club, a.country,
               r.total_score, r.points_behind, r.penalty
        FROM results r
        JOIN athletes a ON a.id = r.athlete_id
        WHERE r.category_id = ?
        ORDER BY r.rank
        """,
        conn, params=(cat_id,),
    )

st.dataframe(df, use_container_width=True)
