import pandas as pd
import streamlit as st

import db.database as database

st.title("Clubs")

database.init_schema()

with database.get_connection() as conn:
    clubs = pd.read_sql("SELECT DISTINCT club FROM athletes ORDER BY club", conn)

if clubs.empty:
    st.info("No data yet — import PDFs on the Import page.")
    st.stop()

club = st.selectbox("Club", clubs["club"].tolist())

with database.get_connection() as conn:
    athletes_df = pd.read_sql(
        "SELECT name, year_of_birth, country FROM athletes WHERE club = ? ORDER BY name",
        conn,
        params=(club,),
    )

if athletes_df.empty:
    st.info("No athletes found for this club.")
    st.stop()

# ── Athletes ──────────────────────────────────────────────────────────────────

st.subheader("Athletes")
st.dataframe(athletes_df, use_container_width=True)

# ── Medal tally ───────────────────────────────────────────────────────────────

st.subheader("Medal tally")

with database.get_connection() as conn:
    results_df = pd.read_sql(
        """
        SELECT r.rank FROM results r
        JOIN athletes a ON a.id = r.athlete_id
        WHERE a.club = ?
        """,
        conn,
        params=(club,),
    )

if not results_df.empty:
    medals = (
        results_df[results_df["rank"] <= 3]
        .groupby("rank")
        .size()
        .reset_index(name="count")
    )
    medals["medal"] = medals["rank"].map({1: "🥇 Gold", 2: "🥈 Silver", 3: "🥉 Bronze"})
    st.dataframe(medals[["medal", "count"]], use_container_width=True)

# ── Ranking ───────────────────────────────────────────────────────────────────

st.subheader("Ranking")
mode = st.radio("Ranking mode", ["Overall", "By year of birth"], horizontal=True)
by_year = mode == "By year of birth"

rank_df = database.get_club_rankings(club)

if rank_df.empty:
    st.info("No ranking data available.")
    st.stop()

rank_col = "rank_by_year" if by_year else "rank_overall"
fig_rank_col = "fig_rank_by_year" if by_year else "fig_rank_overall"

# Build long format: one row per (athlete, competition, metric)
ovr = rank_df.drop_duplicates(["athlete_name", "competition"])[[
    "athlete_name", "year_of_birth", "competition", "date", rank_col,
]].copy()
ovr["metric"] = "Overall"
ovr["rank"] = ovr[rank_col]

figs = rank_df[[
    "athlete_name", "year_of_birth", "competition", "date", "figure_number", fig_rank_col,
]].copy()
figs["metric"] = figs["figure_number"]
figs["rank"] = figs[fig_rank_col]

long = pd.concat([
    ovr[["athlete_name", "year_of_birth", "competition", "date", "metric", "rank"]],
    figs[["athlete_name", "year_of_birth", "competition", "date", "metric", "rank"]],
])

# Pivot to (athlete, yob) × (competition, metric)
wide = long.pivot_table(
    index=["athlete_name", "year_of_birth"],
    columns=["competition", "metric"],
    values="rank",
    aggfunc="first",
)
wide.columns.names = [None, None]
wide.index.names = ["Athlete", "Born"]

# Sort rows: by year of birth first in by-year mode, else by name
if by_year:
    wide = wide.sort_index(level=["Born", "Athlete"])
else:
    wide = wide.sort_index(level="Athlete")

# Sort columns: competitions chronologically, within each comp Overall first then F1 F2…
comp_date = rank_df.drop_duplicates("competition").set_index("competition")["date"].to_dict()
sorted_comps = sorted(wide.columns.get_level_values(0).unique(), key=lambda c: comp_date[c])

new_cols = []
for comp in sorted_comps:
    metrics = list(wide[comp].columns)
    fig_metrics = sorted([m for m in metrics if m != "Overall"], key=lambda x: int(x[1:]))
    for m in (["Overall"] if "Overall" in metrics else []) + fig_metrics:
        new_cols.append((comp, m))
wide = wide[new_cols]

# Style figure rank cells relative to overall rank in the same competition
def _style_row(row: pd.Series) -> list[str]:
    styles = []
    for comp, metric in row.index:
        val = row[(comp, metric)]
        if metric == "Overall" or pd.isna(val):
            styles.append("")
            continue
        overall = row[(comp, "Overall")]
        if pd.isna(overall):
            styles.append("")
        elif int(val) < int(overall):
            styles.append("background-color: #DCFCE7; color: #166534")
        elif int(val) > int(overall):
            styles.append("background-color: #FEE2E2; color: #991B1B")
        else:
            styles.append("background-color: #F3F4F6; color: #4B5563")
    return styles

styled = wide.style.apply(_style_row, axis=1).format("{:.0f}", na_rep="—")
st.dataframe(styled, use_container_width=True)
