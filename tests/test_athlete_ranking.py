import pandas as pd
import pytest
from ui.components import build_ranking_table, style_rank_row


@pytest.fixture
def raw_rank_df():
    return pd.DataFrame([
        {"competition": "Cup A", "date": "2026-01-01",
         "rank_overall": 3, "rank_by_year": 2,
         "figure_number": "F1", "fig_rank_overall": 1, "fig_rank_by_year": 1},
        {"competition": "Cup A", "date": "2026-01-01",
         "rank_overall": 3, "rank_by_year": 2,
         "figure_number": "F2", "fig_rank_overall": 5, "fig_rank_by_year": 4},
        {"competition": "Cup A", "date": "2026-01-01",
         "rank_overall": 3, "rank_by_year": 2,
         "figure_number": "F3", "fig_rank_overall": 3, "fig_rank_by_year": 2},
    ])


def test_build_ranking_table_overall_selects_correct_columns(raw_rank_df):
    wide, fig_cols = build_ranking_table(raw_rank_df, by_year=False)
    assert "overall_rank" in wide.columns
    assert wide.iloc[0]["overall_rank"] == 3
    assert set(fig_cols) == {"F1", "F2", "F3"}
    assert wide.iloc[0]["F1"] == 1
    assert wide.iloc[0]["F2"] == 5


def test_build_ranking_table_by_year_selects_correct_columns(raw_rank_df):
    wide, fig_cols = build_ranking_table(raw_rank_df, by_year=True)
    assert wide.iloc[0]["overall_rank"] == 2  # rank_by_year
    assert wide.iloc[0]["F1"] == 1
    assert wide.iloc[0]["F2"] == 4            # fig_rank_by_year


def test_style_rank_row_green_when_figure_better():
    row = pd.Series({"competition": "Cup", "date": "2026-01-01",
                     "overall_rank": 3, "F1": 1, "F2": 5, "F3": 3})
    styles = style_rank_row(row, ["F1", "F2", "F3"])
    assert styles[3] == "background-color: #DCFCE7; color: #166534"  # F1 < 3


def test_style_rank_row_red_when_figure_worse():
    row = pd.Series({"competition": "Cup", "date": "2026-01-01",
                     "overall_rank": 3, "F1": 1, "F2": 5, "F3": 3})
    styles = style_rank_row(row, ["F1", "F2", "F3"])
    assert styles[4] == "background-color: #FEE2E2; color: #991B1B"  # F2 > 3


def test_style_rank_row_grey_when_figure_equal():
    row = pd.Series({"competition": "Cup", "date": "2026-01-01",
                     "overall_rank": 3, "F1": 1, "F2": 5, "F3": 3})
    styles = style_rank_row(row, ["F1", "F2", "F3"])
    assert styles[5] == "background-color: #F3F4F6; color: #4B5563"  # F3 == 3


def test_style_rank_row_empty_for_non_figure_columns():
    row = pd.Series({"competition": "Cup", "date": "2026-01-01",
                     "overall_rank": 3, "F1": 1})
    styles = style_rank_row(row, ["F1"])
    assert styles[0] == ""  # competition
    assert styles[1] == ""  # date
    assert styles[2] == ""  # overall_rank


def test_style_rank_row_empty_for_nan():
    row = pd.Series({"competition": "Cup", "date": "2026-01-01",
                     "overall_rank": 3, "F1": float("nan")})
    styles = style_rank_row(row, ["F1"])
    assert styles[3] == ""


def test_display_table_shows_rank_over_field_size_but_styles_numerically():
    from ui.components import ranking_display
    df = pd.DataFrame([
        {"competition": "Cup A", "date": "2026-01-01", "rank_overall": 3, "rank_by_year": 2,
         "field_size": 78, "field_size_by_year": 9,
         "figure_number": "F1", "fig_rank_overall": 1, "fig_rank_by_year": 1},
        {"competition": "Cup A", "date": "2026-01-01", "rank_overall": 3, "rank_by_year": 2,
         "field_size": 78, "field_size_by_year": 9,
         "figure_number": "F2", "fig_rank_overall": 5, "fig_rank_by_year": 4},
    ])
    wide, fig_cols = build_ranking_table(df, by_year=False)
    shown, styler = ranking_display(wide, fig_cols)
    assert shown.iloc[0]["overall_rank"] == "3 / 78"
    assert shown.iloc[0]["F1"] == 1
    assert "field_size" not in shown.columns
    css = styler._compute().ctx
    assert "#DCFCE7" in str(css) and "#FEE2E2" in str(css)
    wide, fig_cols = build_ranking_table(df, by_year=True)
    shown, _ = ranking_display(wide, fig_cols)
    assert shown.iloc[0]["overall_rank"] == "2 / 9"
