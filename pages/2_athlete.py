import pandas as pd
import plotly.express as px
import streamlit as st

import db.database as database

st.title("Athletes")

database.init_schema()

with database.get_connection() as conn:
    athletes = pd.read_sql(
        "SELECT id, name, club, country, year_of_birth FROM athletes ORDER BY name",
        conn,
    )

if athletes.empty:
    st.info("No data yet — import PDFs on the Import page.")
    st.stop()

name = st.selectbox("Athlete", athletes["name"].tolist())
row = athletes[athletes["name"] == name].iloc[0]
st.caption(f"{row['club']} · {row['country']} · born {row['year_of_birth']}")

with database.get_connection() as conn:
    df = pd.read_sql(
        """
        SELECT c.name AS competition, c.date, cat.name AS category,
               r.rank, r.total_score, r.points_behind
        FROM results r
        JOIN athletes a ON a.id = r.athlete_id
        JOIN categories cat ON cat.id = r.category_id
        JOIN competitions c ON c.id = cat.competition_id
        WHERE a.name = ?
        ORDER BY c.date
        """,
        conn,
        params=(name,),
    )

if df.empty:
    st.info("No results found for this athlete.")
    st.stop()

st.dataframe(df, use_container_width=True)

fig = px.line(
    df, x="date", y="total_score", markers=True,
    title="Total score over time", labels={"total_score": "Score", "date": "Date"},
)
st.plotly_chart(fig, use_container_width=True)

with database.get_connection() as conn:
    fig_df = pd.read_sql(
        """
        SELECT c.date, c.name AS competition, f.number AS figure,
               fr.score AS figure_score
        FROM figure_results fr
        JOIN results r ON r.id = fr.result_id
        JOIN figures f ON f.id = fr.figure_id
        JOIN athletes a ON a.id = r.athlete_id
        JOIN categories cat ON cat.id = r.category_id
        JOIN competitions c ON c.id = cat.competition_id
        WHERE a.name = ?
        ORDER BY c.date, f.number
        """,
        conn,
        params=(name,),
    )

if not fig_df.empty:
    fig2 = px.bar(
        fig_df, x="competition", y="figure_score", color="figure",
        barmode="group", title="Figure scores per competition",
    )
    st.plotly_chart(fig2, use_container_width=True)
