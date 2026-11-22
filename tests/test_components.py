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




def test_render_column_filters_filters_text_and_numeric_columns():
    from streamlit.testing.v1 import AppTest

    def app():
        import pandas as pd
        import streamlit as st
        from ui.components import render_column_filters
        df = pd.DataFrame({"club": ["A", "B", "A"], "rank": [1, 2, 3], "total_score": [10.0, 20.0, 30.0]})
        out = render_column_filters(df, key="t")
        st.text(f"rows={len(out)}")

    at = AppTest.from_function(app, default_timeout=20).run()
    assert not at.exception
    assert at.text[0].value == "rows=3"

    at.multiselect[0].set_value(["A"]).run()
    assert at.text[0].value == "rows=2"
