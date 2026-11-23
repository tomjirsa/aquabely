import html

import pandas as pd
import streamlit as st

from api.services.scoring import rank_label, trimmed_flags  # noqa: F401

rank_with_field_size = rank_label


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


JUDGE_COLORS = ["#0E7490", "#F59E0B", "#10B981", "#6366F1", "#EF4444", "#64748B", "#8B5CF6"]


def judge_mark_values(row: pd.Series, judge_cols: list[str]) -> list[float | None]:
    return [None if pd.isna(row[c]) else float(row[c]) for c in judge_cols]


def figure_marks_table_html(fig_df: pd.DataFrame, judge_cols: list[str], overall_rank) -> str:
    """Figure table for one competition: difficulty, every judge mark (highest and lowest
    struck through), trimmed average, score and figure rank coloured against the overall rank."""
    judge_heads = "".join(f"<th>J{c.split('_')[1]}</th>" for c in judge_cols)
    rows = []
    for _, row in fig_df.iterrows():
        marks = judge_mark_values(row, judge_cols)
        flags, avg = trimmed_flags(marks)
        cells = []
        for value, dropped in zip(marks, flags):
            if value is None:
                cells.append("<td></td>")
            elif dropped:
                cells.append(f"<td><s>{value:.1f}</s></td>")
            else:
                cells.append(f"<td>{value:.1f}</td>")
        rank = row["fig_rank"]
        if pd.isna(rank):
            rank_cell = "<td></td>"
        else:
            if pd.isna(overall_rank):
                cls = "aq-tbl-eq"
            else:
                cls = ("aq-tbl-good" if int(rank) < int(overall_rank)
                       else "aq-tbl-bad" if int(rank) > int(overall_rank) else "aq-tbl-eq")
            text = rank_with_field_size(rank, row["fig_field_size"])
            rank_cell = f'<td><span class="aq-tbl-rank {cls}">{html.escape(text)}</span></td>'
        avg_cell = "<td></td>" if avg is None else f"<td>{avg:.2f}</td>"
        rows.append(
            f"<tr><td>{html.escape(str(row['figure_name']))}</td>"
            f"<td>{row['coefficient']:.1f}</td>{''.join(cells)}{avg_cell}"
            f"<td class=\"aq-fig-score\">{row['figure_score']:.2f}</td>{rank_cell}</tr>")
    total_difficulty = float(fig_df["coefficient"].sum())
    total_score = float(fig_df["figure_score"].sum())
    blanks = "<td></td>" * len(judge_cols)
    foot = (f"<tr><td>Total</td><td>{total_difficulty:.1f}</td>{blanks}<td></td>"
            f"<td>{total_score:.2f}</td><td></td></tr>")
    return ('<div class="aq-fig-wrap"><table class="aq-fig-table"><thead><tr>'
            f"<th>Figure</th><th>Difficulty</th>{judge_heads}<th>Average</th><th>Score</th><th>Rank</th>"
            f"</tr></thead><tbody>{''.join(rows)}</tbody><tfoot>{foot}</tfoot></table></div>")


TEXT_FILTERS = {"name": "name", "born": "year_of_birth", "club": "club", "country": "country"}
RANGE_FILTERS = {"score": "total_score", "penalty": "penalty", "behind": "points_behind"}
_PLACE_RANK_CLASS = {1: "aq-tbl-good", 2: "aq-tbl-eq", 3: "aq-tbl-bad"}


def parse_range(text: str | None) -> tuple[float, float] | None:
    """'10-20' -> (10, 20); '10-' -> (10, inf); '-5' -> (-inf, 5); '10' -> (10, 10); blank or junk -> None."""
    text = (text or "").strip()
    if not text:
        return None
    if "-" in text:
        low_text, high_text = (part.strip() for part in text.split("-", 1))
    else:
        low_text = high_text = text
    try:
        low = float(low_text) if low_text else float("-inf")
        high = float(high_text) if high_text else float("inf")
    except ValueError:
        return None
    return low, high


def filter_results(df: pd.DataFrame, filters: dict[str, str]) -> pd.DataFrame:
    """Keep the rows matching every filter: substring for text columns, min-max for numbers."""
    out = df
    for key, column in TEXT_FILTERS.items():
        query = (filters.get(key) or "").strip().lower()
        if query:
            out = out[out[column].astype(str).str.lower().str.contains(query, regex=False)]
    for key, column in RANGE_FILTERS.items():
        bounds = parse_range(filters.get(key))
        if bounds:
            out = out[out[column].between(*bounds)]
    return out


def _num(value, fmt: str = "{:.2f}") -> str:
    return "" if pd.isna(value) else fmt.format(value)


def results_table_html(df: pd.DataFrame, active: bool) -> str:
    """Results rows. The rank is renumbered 1..n over the rows shown; while a filter is active the
    official rank sits in a grey half of the same pill."""
    body = []
    for position, (_, row) in enumerate(df.iterrows(), start=1):
        colour = _PLACE_RANK_CLASS.get(position, "")
        split = " aq-rank-split" if active else ""
        pill = f'<span class="aq-rank-pos {colour}{split}">{position}</span>'
        if active:
            pill += f'<span class="aq-rank-orig">{_num(row["rank"], "{:.0f}")}</span>'
        body.append(
            "<tr>"
            f'<td><span class="aq-rank">{pill}</span></td>'
            f'<td class="aq-left aq-athlete">{html.escape(str(row["name"]))}</td>'
            f'<td class="aq-left">{_num(row["year_of_birth"], "{:.0f}")}</td>'
            f'<td class="aq-left">{html.escape(str(row["club"]))}</td>'
            f'<td class="aq-left">{html.escape(str(row["country"] or ""))}</td>'
            f'<td>{_num(row["total_score"])}</td>'
            f'<td>{_num(row["penalty"])}</td>'
            f'<td>{_num(row["points_behind"])}</td>'
            "</tr>")
    head = ('<tr><th class="aq-left">Rank</th><th class="aq-left">Name</th><th class="aq-left">Born</th>'
            '<th class="aq-left">Club</th><th class="aq-left">Country</th><th>Total score</th>'
            '<th>Penalty</th><th>Points behind</th></tr>')
    return ('<div class="aq-fig-wrap"><table class="aq-fig-table aq-results">'
            f'<thead>{head}</thead><tbody>{"".join(body)}</tbody></table></div>')


def figure_detail_html(groups: list[tuple[str, pd.DataFrame]], judge_cols: list[str]) -> str:
    """One block per athlete: the name spans its figure rows; each figure row shows the judge marks
    (highest and lowest struck through), the trimmed average and the figure result."""
    judge_heads = "".join(f"<th>J{c.split('_')[1]}</th>" for c in judge_cols)
    body = []
    for name, figs in groups:
        span = len(figs)
        for k, (_, fg) in enumerate(figs.iterrows()):
            marks = judge_mark_values(fg, judge_cols)
            flags, avg = trimmed_flags(marks)
            cells = []
            for value, dropped in zip(marks, flags):
                if value is None:
                    cells.append("<td></td>")
                elif dropped:
                    cells.append(f"<td><s>{value:.1f}</s></td>")
                else:
                    cells.append(f"<td>{value:.1f}</td>")
            name_cell = (f'<td class="aq-left aq-athlete" rowspan="{span}">{html.escape(name)}</td>'
                         if k == 0 else "")
            average = "" if avg is None else f"{avg:.2f}"
            result = _num(fg["figure_score"])
            body.append(
                f"<tr>{name_cell}<td class=\"aq-left\">{html.escape(str(fg['figure_name']))}</td>"
                f"{''.join(cells)}<td>{average}</td><td class=\"aq-fig-score\">{result}</td></tr>")
    head = (f'<tr><th class="aq-left">Athlete</th><th class="aq-left">Figure</th>{judge_heads}'
            '<th>Average</th><th>Result</th></tr>')
    return ('<div class="aq-fig-wrap"><table class="aq-fig-table aq-figure-detail">'
            f'<thead>{head}</thead><tbody>{"".join(body)}</tbody></table></div>')
