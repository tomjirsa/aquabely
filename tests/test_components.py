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
