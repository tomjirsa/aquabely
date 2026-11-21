import html

import pandas as pd
import streamlit as st


def stat_card(label: str, value: str) -> None:
    st.markdown(
        f'<div class="aq-stat-card"><div class="aq-stat-label">{html.escape(label)}</div>'
        f'<div class="aq-stat-value">{html.escape(value)}</div></div>',
        unsafe_allow_html=True,
    )


def build_ranking_table(rank_df: pd.DataFrame, by_year: bool) -> tuple[pd.DataFrame, list[str]]:
    rank_col = "rank_by_year" if by_year else "rank_overall"
    fig_rank_col = "fig_rank_by_year" if by_year else "fig_rank_overall"
    size_col = "field_size_by_year" if by_year else "field_size"
    extra = [size_col] if size_col in rank_df.columns else []
    df = rank_df[["competition", "date", rank_col, *extra, "figure_name", fig_rank_col]].copy()
    df = df.rename(columns={rank_col: "overall_rank", size_col: "field_size",
                            fig_rank_col: "fig_rank"})
    wide = df.pivot_table(
        index=["competition", "date", "overall_rank", *(["field_size"] if extra else [])],
        columns="figure_name",
        values="fig_rank",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    wide = wide.sort_values("date").reset_index(drop=True)
    base = {"competition", "date", "overall_rank", "field_size"}
    fig_cols = list(dict.fromkeys(df["figure_name"]))
    wide = wide[[c for c in wide.columns if c in base] + fig_cols]
    wide[fig_cols] = wide[fig_cols].astype("Int64")
    return wide, fig_cols


def style_rank_row(row: pd.Series, fig_cols: list[str]) -> list[str]:
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


def rank_with_field_size(rank, size) -> str:
    """'rank / size' text; just the rank when the size is unknown."""
    if pd.isna(rank):
        return ""
    if size is None or pd.isna(size):
        return str(int(rank))
    return f"{int(rank)} / {int(size)}"


def ranking_display(wide: pd.DataFrame, fig_cols: list[str]):
    """Display frame (overall as 'rank / N') and a Styler coloured from the numeric ranks."""
    styles = pd.DataFrame(
        [style_rank_row(row, fig_cols) for _, row in wide.iterrows()],
        index=wide.index, columns=wide.columns)
    shown = wide.copy()
    sizes = shown["field_size"] if "field_size" in shown.columns else [None] * len(shown)
    shown["overall_rank"] = [rank_with_field_size(r, n)
                             for r, n in zip(wide["overall_rank"], sizes)]
    shown = shown.drop(columns=["field_size"], errors="ignore")
    styles = styles.drop(columns=["field_size"], errors="ignore")
    return shown, shown.style.apply(lambda _: styles, axis=None)
