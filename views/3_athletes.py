import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from db.database import get_connection, init_schema
from db.queries import (athlete_figure_detail, athlete_figure_scores, athlete_history, athlete_list,
                        athlete_overall_ranks, athlete_rankings, result_judge_marks)
from ui.components import (build_ranking_table, figure_rank_tab_table, judge_marks_table, rank_with_field_size, stat_card)
from ui.theme import inject_theme, plotly_layout

JUDGE_COLS = [f"judge_{i}" for i in range(1, 8)]

inject_theme()
st.title("Athletes")

conn = get_connection()
init_schema(conn)

athletes = athlete_list(conn)
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
history = athlete_history(conn, int(athlete_id))
history_view = history.drop(columns=["result_id", "competition_category_id"])
history_view["rank"] = [rank_with_field_size(r, n)
                        for r, n in zip(history["rank"], history["field_size"])]
st.dataframe(history_view.drop(columns=["field_size"]), hide_index=True, width="stretch")


def _legend_below(fig):
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.3,
                                  xanchor="center", x=0.5))
    return fig


def _x_label(df):
    return df["competition"] + "<br>" + df["date"]


rank_df = athlete_rankings(conn, int(athlete_id))
by_year = st.toggle("Rank within birth year", value=False)
wide = None
fig_cols = []
if rank_df.empty:
    overall = athlete_overall_ranks(conn, int(athlete_id))
    if overall.empty:
        st.caption("No rankings available for this athlete.")
    else:
        st.caption("No figure rankings available; showing overall rank only.")
        wide = overall.rename(
            columns={"rank_by_year" if by_year else "rank_overall": "overall_rank",
                     "field_size_by_year" if by_year else "field_size": "fs"})
        shown = wide[["competition", "date"]].copy()
        shown["overall_rank"] = [rank_with_field_size(r, n)
                                 for r, n in zip(wide["overall_rank"], wide["fs"])]
        st.dataframe(shown, hide_index=True, width="stretch")
else:
    wide, fig_cols = build_ranking_table(rank_df, by_year)
    st.subheader("Figure ranks")
    comps = list(dict.fromkeys(zip(rank_df["date"], rank_df["competition"])))
    tabs = st.tabs([f"{name} ({date})" for date, name in comps])
    for tab, (date, name) in zip(tabs, comps):
        comp_df = rank_df[(rank_df["date"] == date) & (rank_df["competition"] == name)]
        with tab:
            first = comp_df.iloc[0]
            st.markdown("**Overall rank:** " + rank_with_field_size(
                first["rank_by_year" if by_year else "rank_overall"],
                first["field_size_by_year" if by_year else "field_size"]))
            table, styler = figure_rank_tab_table(comp_df, by_year)
            st.dataframe(styler, hide_index=True, width="stretch")

detail = athlete_figure_detail(conn, int(athlete_id))
if not detail.empty:
    st.subheader("Figure detail")
    st.markdown(judge_marks_table(detail))

if wide is not None:
    st.subheader("Positions Over Time")
    chart = wide.copy()
    chart["x_label"] = _x_label(chart)
    x_order = list(dict.fromkeys(chart.sort_values("date")["x_label"]))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chart["x_label"], y=chart["overall_rank"],
                             mode="lines+markers", name="Overall",
                             line=dict(width=3)))
    for col in fig_cols:
        fig.add_trace(go.Scatter(x=chart["x_label"], y=chart[col].astype(float), mode="lines+markers",
                                 name=col, line=dict(width=1.5, dash="dash")))
    fig.update_yaxes(autorange="reversed", title="Rank (lower = better)")
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=x_order)
    _legend_below(fig)
    st.plotly_chart(plotly_layout(fig), width="stretch")

st.subheader("Scores")
if history.empty:
    st.info("No results found for this athlete.")
else:
    hist = history.sort_values("date").copy()
    hist["x_label"] = _x_label(hist)
    fig1 = px.line(hist, x="x_label", y="total_score", markers=True,
                   title="Total score over time",
                   labels={"total_score": "Score", "x_label": ""},
                   category_orders={"x_label": list(dict.fromkeys(hist["x_label"]))})
    st.plotly_chart(plotly_layout(_legend_below(fig1)), width="stretch")

    fig_df = athlete_figure_scores(conn, int(athlete_id))
    if not fig_df.empty:
        fig_df = fig_df.sort_values("date")
        fig_df["figure_label"] = fig_df["figure_name"]
        fig_df["x_label"] = _x_label(fig_df)
        fig_order = list(dict.fromkeys(fig_df["figure_label"]))
        comp_order = list(dict.fromkeys(fig_df["competition"]))
        x_order = list(dict.fromkeys(fig_df["x_label"]))

        fig2 = px.line(fig_df, x="x_label", y="figure_score", color="figure_label",
                       markers=True, title="Figure scores over time",
                       labels={"figure_score": "Score", "x_label": "", "figure_label": "Figure"},
                       category_orders={"figure_label": fig_order, "x_label": x_order})
        st.plotly_chart(plotly_layout(_legend_below(fig2)), width="stretch")

        fig3 = px.bar(fig_df, x="competition", y="figure_score", color="figure_label",
                      barmode="group", title="Figure scores per competition",
                      labels={"figure_label": "Figure", "figure_score": "Score"},
                      category_orders={"figure_label": fig_order, "competition": comp_order})
        st.plotly_chart(plotly_layout(_legend_below(fig3)), width="stretch")

        st.subheader("Judge marks per figure")
        opts = {int(r.result_id): f"{r.competition} ({r.age_group}, {r.date})"
                for r in history.itertuples()}
        result_id = st.selectbox("Competition", list(opts), format_func=opts.get,
                                 key="judge_marks_comp")
        marks = result_judge_marks(conn, int(result_id))
        marks = marks.melt(
            id_vars=["figure_name"],
            value_vars=[c for c in JUDGE_COLS if marks[c].notna().any()],
            var_name="judge", value_name="mark").dropna(subset=["mark"])
        if marks.empty:
            st.caption("No judge marks for this competition.")
        else:
            marks["figure_label"] = marks["figure_name"]
            marks["judge"] = marks["judge"].str.replace("judge_", "J", regex=False)
            fig4 = px.bar(
                marks, x="figure_label", y="mark", color="judge", barmode="group",
                title=f"Judge marks - {opts[int(result_id)]}",
                labels={"figure_label": "Figure", "mark": "Mark", "judge": "Judge"},
                category_orders={"figure_label": list(
                    dict.fromkeys(marks["figure_label"]))})
            fig4.update_layout(yaxis_range=[0, 10])
            st.plotly_chart(plotly_layout(_legend_below(fig4)), width="stretch")
conn.close()
