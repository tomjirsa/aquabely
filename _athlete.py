import pandas as pd


def _build_ranking_table(rank_df: pd.DataFrame, by_year: bool) -> tuple[pd.DataFrame, list[str]]:
    rank_col = "rank_by_year" if by_year else "rank_overall"
    fig_rank_col = "fig_rank_by_year" if by_year else "fig_rank_overall"
    df = rank_df[["competition", "date", rank_col, "figure_number", fig_rank_col]].copy()
    df = df.rename(columns={rank_col: "overall_rank", fig_rank_col: "fig_rank"})
    wide = df.pivot_table(
        index=["competition", "date", "overall_rank"],
        columns="figure_number",
        values="fig_rank",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    wide = wide.sort_values("date").reset_index(drop=True)
    fig_cols = [c for c in wide.columns if str(c).startswith("F")]
    return wide, fig_cols


def _style_rank_row(row: pd.Series, fig_cols: list[str]) -> list[str]:
    overall = row["overall_rank"]
    styles = []
    for col in row.index:
        if col not in fig_cols or pd.isna(row[col]):
            styles.append("")
        elif int(row[col]) < int(overall):
            styles.append("background-color: #DCFCE7; color: #166534")
        elif int(row[col]) > int(overall):
            styles.append("background-color: #FEE2E2; color: #991B1B")
        else:
            styles.append("background-color: #F3F4F6; color: #4B5563")
    return styles
