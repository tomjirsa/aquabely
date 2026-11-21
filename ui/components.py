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


def figure_rank_tab_table(comp_df: pd.DataFrame, by_year: bool):
    """Per-figure rows (figure, rank, of) for one competition, rank coloured vs the overall rank."""
    rank_col = "fig_rank_by_year" if by_year else "fig_rank_overall"
    size_col = "fig_field_size_by_year" if by_year else "fig_field_size"
    overall = comp_df["rank_by_year" if by_year else "rank_overall"].iloc[0]
    df = comp_df[["figure_name", rank_col, size_col]].rename(
        columns={"figure_name": "figure", rank_col: "rank", size_col: "of"})
    df = df.reset_index(drop=True).astype({"rank": "Int64", "of": "Int64"})
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    styles["rank"] = [style_rank_row(pd.Series({"overall_rank": overall, "rank": r}), ["rank"])[1]
                      for r in df["rank"]]
    return df, df.style.apply(lambda _: styles, axis=None)


def figure_rank_tab_html(comp_df: pd.DataFrame, by_year: bool) -> str:
    """Card-style HTML table (figure, rank, of) for one competition; classes styled in ui/theme.py."""
    df, _ = figure_rank_tab_table(comp_df, by_year)
    overall = comp_df["rank_by_year" if by_year else "rank_overall"].iloc[0]
    rows = []
    for fig, rank, size in zip(df["figure"], df["rank"], df["of"]):
        if pd.isna(rank):
            rank_cell, cls = "", ""
        else:
            cls = ("aq-tbl-good" if int(rank) < int(overall)
                   else "aq-tbl-bad" if int(rank) > int(overall) else "aq-tbl-eq")
            rank_cell = html.escape(str(int(rank)))
        size_cell = "" if pd.isna(size) else html.escape(str(int(size)))
        rows.append(
            f'<div class="aq-tbl-row"><div class="aq-tbl-cell aq-tbl-name">{html.escape(str(fig))}</div>'
            f'<div class="aq-tbl-cell"><span class="aq-tbl-rank {cls}">{rank_cell}</span></div>'
            f'<div class="aq-tbl-cell aq-tbl-of">{size_cell}</div></div>')
    head = ('<div class="aq-tbl-head"><div class="aq-tbl-cell">Figure</div>'
            '<div class="aq-tbl-cell">Rank</div><div class="aq-tbl-cell">Of</div></div>')
    return f'<div class="aq-tbl">{head}{"".join(rows)}</div>'


JUDGE_COLS = [f"judge_{i}" for i in range(1, 8)]


def trimmed_flags(scores: list[float | None]) -> tuple[list[bool], float | None]:
    """Flag the single lowest and single highest mark as struck; return the trimmed mean."""
    present = [i for i, s in enumerate(scores) if s is not None and s == s]
    flags = [False] * len(scores)
    if len(present) < 3:
        return flags, None
    lo = min(present, key=lambda i: (scores[i], i))
    hi = max((i for i in present if i != lo), key=lambda i: (scores[i], -i))
    # With ties the first max must differ from lo; otherwise pick the first max among the rest.
    flags[lo] = flags[hi] = True
    kept = [scores[i] for i in present if not flags[i]]
    return flags, sum(kept) / len(kept)


def judges_markdown(scores: list[float | None]) -> str:
    flags, avg = trimmed_flags(scores)
    parts = [f"~~{s}~~" if flags[i] else str(s)
             for i, s in enumerate(scores) if s is not None and s == s]
    text = " ".join(parts)
    if avg is not None:
        text += f" → avg {avg:.2f}"
    return text


def judge_marks_table(df: pd.DataFrame, label: str = "judge marks") -> str:
    """Markdown table of df without judge columns plus one struck-through marks column."""
    others = [c for c in df.columns if c not in JUDGE_COLS]
    jcols = [c for c in JUDGE_COLS if c in df.columns]

    def cell(v) -> str:
        if v is None or (isinstance(v, float) and v != v):
            return ""
        return str(v).replace("|", "\|")

    lines = ["| " + " | ".join([*others, label]) + " |",
             "|" + "---|" * (len(others) + 1)]
    for _, row in df.iterrows():
        marks = judges_markdown([None if row[c] != row[c] else row[c] for c in jcols])
        lines.append("| " + " | ".join([*(cell(row[c]) for c in others), marks]) + " |")
    return "\n".join(lines)
