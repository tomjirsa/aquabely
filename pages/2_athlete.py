import pandas as pd
import plotly.express as px
import streamlit as st

import db.database as database
from pages._athlete import _build_ranking_table, _style_rank_row

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
athlete_id = int(row["id"])

# ── Ranking ──────────────────────────────────────────────────────────────────

st.subheader("Ranking")
mode = st.radio("Ranking mode", ["Overall", "By year of birth"], horizontal=True)
by_year = mode == "By year of birth"

rank_df = database.get_athlete_rankings(athlete_id)

if rank_df.empty:
    st.info("No ranking data available.")
else:
    wide, fig_cols = _build_ranking_table(rank_df, by_year)
    rank_label = "By-year rank" if by_year else "Overall rank"

    display = wide.rename(columns={"overall_rank": rank_label})

    def _style_display_row(row):
        return _style_rank_row(row.rename({rank_label: "overall_rank"}), fig_cols)

    styled = (
        display.style
        .apply(_style_display_row, axis=1)
        .format(na_rep="—", subset=fig_cols)
    )
    st.dataframe(styled, use_container_width=True)

    chart_df = wide.melt(
        id_vars=["competition", "date"],
        value_vars=["overall_rank"] + fig_cols,
        var_name="series",
        value_name="rank",
    )
    chart_df["series"] = chart_df["series"].replace("overall_rank", "Overall")
    date_order = list(dict.fromkeys(chart_df.sort_values("date")["date"]))

    fig_pos = px.line(
        chart_df.dropna(subset=["rank"]),
        x="date",
        y="rank",
        color="series",
        markers=True,
        title="Positions over time",
        labels={"rank": "Rank", "date": "Date", "series": ""},
        category_orders={"date": date_order},
    )
    fig_pos.update_yaxes(autorange="reversed", title="Rank (lower = better)")
    for trace in fig_pos.data:
        if trace.name == "Overall":
            trace.line.width = 3
        else:
            trace.line.dash = "dash"
            trace.line.width = 1.5
    fig_pos.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5))
    st.plotly_chart(fig_pos, use_container_width=True)

# ── Scores ────────────────────────────────────────────────────────────────────

st.subheader("Scores")

with database.get_connection() as conn:
    df = pd.read_sql(
        """
        SELECT c.name AS competition, c.date, cat.name AS category,
               r.rank, r.total_score, r.points_behind
        FROM results r
        JOIN athletes a ON a.id = r.athlete_id
        JOIN categories cat ON cat.id = r.category_id
        JOIN competitions c ON c.id = cat.competition_id
        WHERE a.id = ?
        ORDER BY c.date
        """,
        conn,
        params=(athlete_id,),
    )

if df.empty:
    st.info("No results found for this athlete.")
    st.stop()

st.dataframe(df, use_container_width=True)

df = df.sort_values("date")
fig = px.line(
    df, x="date", y="total_score", markers=True,
    title="Total score over time",
    labels={"total_score": "Score", "date": "Date"},
)
fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5))
st.plotly_chart(fig, use_container_width=True)

with database.get_connection() as conn:
    fig_df = pd.read_sql(
        """
        SELECT c.date, c.name AS competition, f.number AS figure,
               f.name AS figure_name, fr.score AS figure_score
        FROM figure_results fr
        JOIN results r ON r.id = fr.result_id
        JOIN figures f ON f.id = fr.figure_id
        JOIN athletes a ON a.id = r.athlete_id
        JOIN categories cat ON cat.id = r.category_id
        JOIN competitions c ON c.id = cat.competition_id
        WHERE a.id = ?
        ORDER BY c.date, f.number
        """,
        conn,
        params=(athlete_id,),
    )

if not fig_df.empty:
    fig_df = fig_df.sort_values("date")
    fig_df["figure_label"] = fig_df["figure"] + ": " + fig_df["figure_name"]
    fig_order = sorted(
        fig_df["figure_label"].unique(),
        key=lambda x: int(x[1:x.index(":")]),
    )
    comp_order = list(dict.fromkeys(fig_df.sort_values("date")["competition"]))

    fig2 = px.line(
        fig_df, x="date", y="figure_score", color="figure_label", markers=True,
        title="Figure scores over time",
        labels={"figure_score": "Score", "date": "Date", "figure_label": "Figure"},
        category_orders={"figure_label": fig_order},
    )
    fig2.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5))
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.bar(
        fig_df, x="competition", y="figure_score", color="figure_label",
        barmode="group", title="Figure scores per competition",
        labels={"figure_label": "Figure", "figure_score": "Score"},
        category_orders={"figure_label": fig_order, "competition": comp_order},
    )
    fig3.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5))
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Judge marks per figure")
    competitions = sorted(fig_df["competition"].unique())
    selected_comp = st.selectbox("Competition", competitions, key="judge_marks_comp")

    with database.get_connection() as conn:
        marks_df = pd.read_sql(
            """
            SELECT f.number AS figure, f.name AS figure_name,
                   fr.judge_1, fr.judge_2, fr.judge_3, fr.judge_4,
                   fr.judge_5, fr.judge_6, fr.judge_7
            FROM figure_results fr
            JOIN results r ON r.id = fr.result_id
            JOIN figures f ON f.id = fr.figure_id
            JOIN athletes a ON a.id = r.athlete_id
            JOIN categories cat ON cat.id = r.category_id
            JOIN competitions c ON c.id = cat.competition_id
            WHERE a.id = ? AND c.name = ?
            ORDER BY f.number
            """,
            conn,
            params=(athlete_id, selected_comp),
        )

    judge_cols = [
        "judge_1", "judge_2", "judge_3", "judge_4",
        "judge_5", "judge_6", "judge_7",
    ]
    marks_df = marks_df.melt(
        id_vars=["figure", "figure_name"],
        value_vars=[c for c in judge_cols if marks_df[c].notna().any()],
        var_name="judge",
        value_name="mark",
    ).dropna(subset=["mark"])
    marks_df["figure_label"] = marks_df["figure"] + ": " + marks_df["figure_name"]
    marks_df["judge"] = marks_df["judge"].str.replace("judge_", "J", regex=False)

    fig4 = px.bar(
        marks_df, x="figure_label", y="mark", color="judge", barmode="group",
        title=f"Judge marks — {selected_comp}",
        labels={"figure_label": "Figure", "mark": "Mark", "judge": "Judge"},
        category_orders={
            "figure_label": sorted(
                marks_df["figure_label"].unique(),
                key=lambda x: int(x[1:x.index(":")]),
            )
        },
    )
    fig4.update_layout(yaxis_range=[0, 10], legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5))
    st.plotly_chart(fig4, use_container_width=True)
