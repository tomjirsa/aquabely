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

comp_order = list(dict.fromkeys(df.sort_values("date")["competition"]))
avg = df.groupby("competition")["total_score"].mean().reset_index()
fig = px.bar(
    avg, x="competition", y="total_score",
    title="Avg score per competition", labels={"total_score": "Avg score"},
    category_orders={"competition": comp_order},
)
fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5))
col2.plotly_chart(fig, use_container_width=True)

with database.get_connection() as conn:
    fig_df = pd.read_sql(
        """
        SELECT f.number AS figure, f.name AS figure_name,
               fr.score, c.name AS competition, c.date
        FROM figure_results fr
        JOIN results r ON r.id = fr.result_id
        JOIN athletes a ON a.id = r.athlete_id
        JOIN figures f ON f.id = fr.figure_id
        JOIN categories cat ON cat.id = r.category_id
        JOIN competitions c ON c.id = cat.competition_id
        WHERE a.club = ?
        ORDER BY c.date, f.number
        """,
        conn,
        params=(club,),
    )

if not fig_df.empty:
    fig_df = fig_df.sort_values("date")
    avg_time = (
        fig_df.groupby(["date", "figure", "figure_name"])["score"]
        .mean()
        .reset_index()
        .sort_values("date")
    )
    avg_time["figure_label"] = avg_time["figure"] + ": " + avg_time["figure_name"]
    fig_order = sorted(avg_time["figure_label"].unique(), key=lambda x: int(x[1:x.index(":")]))
    avg_chart = px.line(
        avg_time, x="date", y="score", color="figure_label", markers=True,
        title="Avg figure score over time",
        labels={"date": "Date", "score": "Avg score", "figure_label": "Figure"},
        category_orders={"figure_label": fig_order},
    )
    avg_chart.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5))
    st.plotly_chart(avg_chart, use_container_width=True)

    st.subheader("Score distribution by figure")
    fig_df = fig_df.sort_values("figure")
    y_min = 0
    y_max = 20
    competitions = sorted(fig_df["competition"].unique())
    for comp in competitions:
        subset = fig_df[fig_df["competition"] == comp]
        chart = px.box(
            subset, x="figure", y="score",
            title=comp,
            labels={"figure": "Figure", "score": "Score"},
            points="all",
            hover_data=["figure_name"],
            category_orders={"figure": sorted(subset["figure"].unique(), key=lambda x: int(x[1:]))},
        )
        chart.update_traces(boxmean=True)
        chart.update_layout(
            yaxis_range=[y_min, y_max],
            margin=dict(t=40, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5),
        )
        st.plotly_chart(chart, use_container_width=True)
