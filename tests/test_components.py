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
