import pytest

from ui.components import judges_markdown, trimmed_flags


def test_trimmed_flags_example():
    flags, avg = trimmed_flags([6.1, 6.2, 6.4, 6.2, 6.2, 6.2, 6.2])
    assert [i for i, f in enumerate(flags) if f] == [0, 2]
    assert avg == pytest.approx(6.2, abs=1e-9)


def test_trimmed_flags_all_equal_three():
    flags, avg = trimmed_flags([5, 5, 5])
    assert [i for i, f in enumerate(flags) if f] == [0, 1]
    assert avg == 5.0


def test_trimmed_flags_too_few():
    flags, avg = trimmed_flags([5, None, 6])
    assert not any(flags)
    assert avg is None


def test_trimmed_flags_four_equal():
    flags, avg = trimmed_flags([7, 7, 7, 7])
    assert sum(flags) == 2
    assert avg == 7.0


def test_judges_markdown():
    md = judges_markdown([6.1, 6.2, 6.4, 6.2, 6.2, 6.2, 6.2])
    assert "~~6.1~~" in md and "~~6.4~~" in md and "avg 6.20" in md


def _comp_df(fig_ranks, overall=3, name="Ballet"):
    import pandas as pd
    return pd.DataFrame({
        "figure_name": [name] * len(fig_ranks) if isinstance(name, str) else name,
        "fig_rank_overall": fig_ranks, "fig_field_size": [10] * len(fig_ranks),
        "fig_rank_by_year": fig_ranks, "fig_field_size_by_year": [10] * len(fig_ranks),
        "rank_overall": [overall] * len(fig_ranks), "rank_by_year": [overall] * len(fig_ranks),
    })


def test_figure_rank_tab_html_rows_and_colours():
    from ui.components import figure_rank_tab_html
    out = figure_rank_tab_html(_comp_df([1, 5, 3], name=["A", "B", "C"]), False)
    assert "aq-tbl-row" in out
    assert "aq-tbl-good" in out and "aq-tbl-bad" in out and "aq-tbl-eq" in out


def test_figure_rank_tab_html_escapes_figure_name():
    from ui.components import figure_rank_tab_html
    out = figure_rank_tab_html(_comp_df([1], name="<b>x</b>"), False)
    assert "<b>" not in out
    assert "&lt;b&gt;" in out


def test_figure_marks_table_strikes_highest_and_lowest_and_averages_the_rest():
    import pandas as pd
    from ui.components import figure_marks_table_html

    df = pd.DataFrame([{
        "figure_name": "Ballet", "coefficient": 2.0,
        "judge_1": 7.0, "judge_2": 8.0, "judge_3": 6.0, "judge_4": 7.5, "judge_5": None,
        "figure_score": 14.0, "fig_rank": 1, "fig_field_size": 3,
    }])
    out = figure_marks_table_html(df, ["judge_1", "judge_2", "judge_3", "judge_4"], overall_rank=1)
    assert "<s>6.0</s>" in out and "<s>8.0</s>" in out
    assert "<s>7.0</s>" not in out and "<s>7.5</s>" not in out
    assert "7.25" in out  # mean of 7.0 and 7.5
    assert "aq-fig-score" in out and "14.00" in out


def test_parse_range_forms():
    from ui.components import parse_range
    assert parse_range("") is None and parse_range("abc") is None
    assert parse_range("10") == (10.0, 10.0)
    assert parse_range("10-20") == (10.0, 20.0)
    assert parse_range("10-") == (10.0, float("inf"))
    assert parse_range("-5") == (float("-inf"), 5.0)


def test_filter_results_text_and_range():
    import pandas as pd
    from ui.components import filter_results
    df = pd.DataFrame({
        "name": ["Ann", "Bea", "Cy"], "year_of_birth": [2015, 2016, 2016],
        "club": ["Delfin", "Kometa", "Delfin"], "country": ["CZE", "SVK", "CZE"],
        "total_score": [40.0, 35.0, 30.0], "penalty": [0.0, 1.0, 0.0], "points_behind": [0.0, 5.0, 10.0]})
    assert list(filter_results(df, {"club": "delf"})["name"]) == ["Ann", "Cy"]
    assert list(filter_results(df, {"born": "2016"})["name"]) == ["Bea", "Cy"]
    assert list(filter_results(df, {"score": "32-40"})["name"]) == ["Ann", "Bea"]
    assert list(filter_results(df, {"penalty": "1-"})["name"]) == ["Bea"]
    assert len(filter_results(df, {"name": "", "score": "junk"})) == 3


def test_results_table_renumbers_and_shows_official_rank_when_filtered():
    import pandas as pd
    from ui.components import results_table_html
    df = pd.DataFrame({
        "rank": [1, 3, 4], "name": ["A", "C", "D"], "year_of_birth": [2015, 2017, 2015],
        "club": ["X", "Y", "Y"], "country": ["CZE", "CZE", "POL"],
        "total_score": [40.0, 30.0, 25.0], "penalty": [0.0, 0.0, 1.0], "points_behind": [0.0, 10.0, 15.0]})
    filtered = results_table_html(df.iloc[[1, 2]], active=True)
    assert '<span class="aq-rank-pos aq-tbl-good aq-rank-split">1</span>' in filtered
    assert '<span class="aq-rank-orig">3</span>' in filtered
    assert '<span class="aq-rank-orig">4</span>' in filtered
    plain = results_table_html(df, active=False)
    assert "aq-rank-orig" not in plain
    assert "aq-rank-split" not in plain


def test_figure_detail_strikes_extremes_and_rowspans_athlete():
    import pandas as pd
    from ui.components import figure_detail_html
    figs = pd.DataFrame([
        {"figure_name": "Ballet", "judge_1": 7.0, "judge_2": 8.0, "judge_3": 6.0,
         "judge_4": 7.5, "judge_5": None, "figure_score": 14.0},
        {"figure_name": "Kipnus", "judge_1": 5.0, "judge_2": 5.0, "judge_3": 5.0,
         "judge_4": 5.0, "judge_5": None, "figure_score": 10.0},
    ])
    out = figure_detail_html([("Ann", figs)], ["judge_1", "judge_2", "judge_3", "judge_4"])
    assert 'rowspan="2"' in out
    assert "<s>6.0</s>" in out and "<s>8.0</s>" in out
    assert "7.25" in out and "14.00" in out
    assert out.count("<tr>") == 3  # header + two figure rows
