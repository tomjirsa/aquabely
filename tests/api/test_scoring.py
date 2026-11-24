import pytest

from api.services.scoring import rank_label, trimmed_flags


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


def test_rank_label_forms():
    assert rank_label(3, 24) == "3 / 24"
    assert rank_label(3, None) == "3"
    assert rank_label(None, 24) == ""


def test_rank_label_nan():
    nan = float("nan")
    assert rank_label(nan, 24) == ""
    assert rank_label(3, nan) == "3"


def test_trimmed_mean_matches_validator():
    marks = [7.0, 8.0, 6.0, 7.5]
    flags, avg = trimmed_flags(marks)
    assert avg == sum(sorted(marks)[1:-1]) / 2
