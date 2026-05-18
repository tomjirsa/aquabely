import pandas as pd
import plotly.express as px
import streamlit as st

import db.database as database

st.title("Clubs")

database.init_schema()

with database.get_connection() as conn:
    clubs = pd.read_sql(
        "SELECT DISTINCT club FROM athletes ORDER BY club", conn
    )

if clubs.empty:
    st.info("No data yet — import PDFs on the Import page.")
    st.stop()

club = st.selectbox("Club", clubs["club"].tolist())

with database.get_connection() as conn:
    df = pd.read_sql(
        """
        SELECT a.name, a.country, c.name AS competition, c.date,
               cat.name AS category, r.rank, r.total_score
        FROM results r
        JOIN athletes a ON a.id = r.athlete_id
        JOIN categories cat ON cat.id = r.category_id
        JOIN competitions c ON c.id = cat.competition_id
        WHERE a.club = ?
        ORDER BY c.date, r.rank
        """,
        conn,
        params=(club,),
    )

if df.empty:
    st.info("No results found for this club.")
    st.stop()

st.dataframe(df, use_container_width=True)

col1, col2 = st.columns(2)

medals = (
    df[df["rank"] <= 3]
    .groupby("rank")
    .size()
    .reset_index(name="count")
)
medals["medal"] = medals["rank"].map({1: "🥇 Gold", 2: "🥈 Silver", 3: "🥉 Bronze"})
col1.subheader("Medal tally")
col1.dataframe(medals[["medal", "count"]], use_container_width=True)

avg = df.groupby("competition")["total_score"].mean().reset_index()
fig = px.bar(
    avg, x="competition", y="total_score",
    title="Avg score per competition", labels={"total_score": "Avg score"},
)
col2.plotly_chart(fig, use_container_width=True)
