import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db.database import get_connection, init_schema
from db.queries import (athlete_figure_detail, athlete_history, athlete_list, athlete_overall_ranks,
                        athlete_rankings, athlete_summaries)
from ui.components import (JUDGE_COLORS, build_ranking_table, figure_marks_table_html, judge_mark_values,
                           rank_with_field_size, stat_card, trimmed_flags)
from ui.theme import inject_theme, plotly_layout

JUDGE_COLS = [f"judge_{i}" for i in range(1, 8)]
FIG_RANK_COLS = ["fig_rank_overall", "fig_rank_by_year", "fig_field_size", "fig_field_size_by_year"]


def _legend_below(fig):
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.3,
                                  xanchor="center", x=0.5))
    return fig


def _x_label(df):
    return df["competition"] + "<br>" + df["date"]


def _score_text(value):
    return "n/a" if pd.isna(value) else f"{value:.2f}"


inject_theme()
st.title("Athletes")

conn = get_connection()
init_schema(conn)

athletes = athlete_list(conn).merge(athlete_summaries(conn), on="id")
if athletes.empty:
    st.info("No athletes yet. Use the Import page to add results.")
    conn.close()
    st.stop()

query = st.text_input("Search athletes or clubs").strip().lower()
found = athletes
if query:
    found = athletes[athletes["name"].str.lower().str.contains(query, regex=False)
                     | athletes["club"].str.lower().str.contains(query, regex=False)]
if found.empty:
    st.warning("No athlete matches that search.")
    conn.close()
    st.stop()

table = found[["name", "club", "competitions", "best_score"]].rename(columns={
    "name": "Athlete", "club": "Club", "competitions": "Competitions", "best_score": "Best score"})
event = st.dataframe(
    table, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
    key="athlete_table", column_config={"Best score": st.column_config.NumberColumn(format="%.2f")})
picked = event.selection.rows
row_idx = picked[0] if picked and picked[0] < len(found) else 0
a = found.iloc[row_idx]
athlete_id = int(a["id"])

history = athlete_history(conn, athlete_id)
rank_df = athlete_rankings(conn, athlete_id)
detail = athlete_figure_detail(conn, athlete_id)

st.subheader(str(a["name"]))
c1, c2, c3, c4 = st.columns(4)
with c1:
    stat_card("Club", str(a["club"]))
with c2:
    yob = a["year_of_birth"]
    stat_card("Born", "n/a" if pd.isna(yob) else str(int(yob)))
with c3:
    stat_card("Competitions", str(int(a["competitions"])))
with c4:
    stat_card("Best / average", f"{_score_text(a['best_score'])} / "
              f"{_score_text(history['total_score'].mean() if not history.empty else None)}")

overview_tab, competitions_tab, history_tab = st.tabs(["Overview", "Competitions", "History"])

with overview_tab:
    if history.empty:
        st.info("No results found for this athlete.")
    else:
        history_view = history.drop(columns=["result_id", "competition_category_id"])
        history_view["rank"] = [rank_with_field_size(r, n)
                                for r, n in zip(history["rank"], history["field_size"])]
        st.dataframe(history_view.drop(columns=["field_size"]), hide_index=True, width="stretch")

        hist = history.sort_values("date").copy()
        hist["x_label"] = _x_label(hist)
        fig1 = go.Figure(go.Scatter(x=hist["x_label"], y=hist["total_score"], mode="lines+markers",
                                    name="Score"))
        fig1.update_layout(title="Total score over time", yaxis_title="Score", xaxis_title="")
        fig1.update_xaxes(type="category")
        st.plotly_chart(plotly_layout(fig1), width="stretch")

        if rank_df.empty:
            overall = athlete_overall_ranks(conn, athlete_id)
            wide = overall.rename(columns={"rank_overall": "overall_rank"})
            fig_cols = []
        else:
            wide, fig_cols = build_ranking_table(rank_df, False)
        chart = wide.copy()
        chart["x_label"] = _x_label(chart)
        x_order = list(dict.fromkeys(chart.sort_values("date")["x_label"]))
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=chart["x_label"], y=chart["overall_rank"],
                                  mode="lines+markers", name="Overall", line=dict(width=3)))
        for col in fig_cols:
            fig2.add_trace(go.Scatter(x=chart["x_label"], y=chart[col].astype(float), mode="lines+markers",
                                      name=col, line=dict(width=1.5, dash="dash")))
        fig2.update_yaxes(autorange="reversed", title="Rank (lower = better)")
        fig2.update_xaxes(type="category", categoryorder="array", categoryarray=x_order)
        st.plotly_chart(plotly_layout(_legend_below(fig2)), width="stretch")

with competitions_tab:
    ranking = st.pills("Ranking", ["Overall", "By year"], default="Overall", key="ranking_mode") or "Overall"
    by_year = ranking == "By year"
    if history.empty:
        st.info("No results found for this athlete.")
    else:
        fig_ranks = (rank_df[["competition", "date", "figure_name", *FIG_RANK_COLS]]
                     .drop_duplicates(["competition", "date", "figure_name"])
                     if not rank_df.empty
                     else pd.DataFrame(columns=["competition", "date", "figure_name", *FIG_RANK_COLS]))
        merged = detail.merge(fig_ranks, on=["competition", "date", "figure_name"], how="left")
        rank_col = "fig_rank_by_year" if by_year else "fig_rank_overall"
        size_col = "fig_field_size_by_year" if by_year else "fig_field_size"

        comps = list(dict.fromkeys(zip(history["date"], history["competition"])))
        for tab, (date, name) in zip(st.tabs([f"{comp} ({day})" for day, comp in comps]), comps):
            with tab:
                rank_row = rank_df[(rank_df["competition"] == name) & (rank_df["date"] == date)]
                if rank_row.empty:
                    past = history[(history["competition"] == name) & (history["date"] == date)].iloc[0]
                    overall_rank, size = past["rank"], past["field_size"]
                elif by_year:
                    overall_rank = rank_row["rank_by_year"].iloc[0]
                    size = rank_row["field_size_by_year"].iloc[0]
                else:
                    overall_rank = rank_row["rank_overall"].iloc[0]
                    size = rank_row["field_size"].iloc[0]
                scope = "by birth year" if by_year else "overall"
                st.markdown(f"**Rank {scope}:** " + rank_with_field_size(overall_rank, size))

                comp_fig = merged[(merged["competition"] == name) & (merged["date"] == date)].copy()
                if comp_fig.empty:
                    st.caption("No figure results for this competition.")
                    continue
                comp_fig["fig_rank"] = comp_fig[rank_col]
                comp_fig["fig_field_size"] = comp_fig[size_col]
                judge_cols = [c for c in JUDGE_COLS if comp_fig[c].notna().any()]
                st.markdown(figure_marks_table_html(comp_fig, judge_cols, overall_rank),
                            unsafe_allow_html=True)
                st.caption("Struck-through marks are the highest and lowest, dropped from the average. "
                           "Average is the trimmed mean of the remaining judges. Score = average × difficulty.")

with history_tab:
    if detail.empty:
        st.info("No figure results for this athlete.")
    else:
        figures = list(dict.fromkeys(detail["figure_name"]))
        for tab, figure in zip(st.tabs(figures), figures):
            with tab:
                fdf = detail[detail["figure_name"] == figure]
                judge_cols = [c for c in JUDGE_COLS if fdf[c].notna().any()]
                x_labels = list(_x_label(fdf))
                marks = [judge_mark_values(r, judge_cols) for _, r in fdf.iterrows()]
                trimmed = [trimmed_flags(m) for m in marks]

                fig = go.Figure()
                for j, col in enumerate(judge_cols):
                    color = JUDGE_COLORS[j % len(JUDGE_COLORS)]
                    fig.add_trace(go.Bar(
                        x=x_labels, y=[m[j] for m in marks], name=f"J{col.split('_')[1]}",
                        marker=dict(color=["#FFFFFF" if flags[j] else color for flags, _ in trimmed],
                                    line=dict(color=color, width=2))))
                fig.add_trace(go.Scatter(
                    x=x_labels, y=[avg for _, avg in trimmed], mode="markers", name="Trimmed average",
                    marker=dict(symbol="line-ew", size=40, color="#0F172A",
                                line=dict(width=3, color="#0F172A"))))
                fig.update_layout(barmode="group", yaxis_range=[0, 10], yaxis_title="Mark")
                fig.update_xaxes(type="category")
                st.plotly_chart(plotly_layout(_legend_below(fig)), width="stretch")
                st.caption("Hollow bars are the highest and lowest marks, dropped from the average. "
                           "The dash on each competition is the trimmed average.")
conn.close()
