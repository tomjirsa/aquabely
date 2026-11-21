import pytest
from parser.figure_match import match_figure, UnmatchedFigureError


def test_code_wins_over_printed_name():
    e = match_figure("U12", "Something Else Entirely", "106")
    assert (e.code, e.name) == ("106", "Straight Ballet Leg")


def test_l3_ballet_leg_names_both_match_101():
    assert match_figure("L3", "Ballet Leg Single", None).code == "101"
    assert match_figure("L3", "Straight Ballet Leg", None).code == "101"


def test_u12_straight_ballet_leg_is_not_l3_101():
    assert match_figure("U12", "Straight Ballet Leg", "106").code == "106"


def test_unknown_figure_raises_with_name():
    with pytest.raises(UnmatchedFigureError) as exc:
        match_figure("L3", "Mystery Spin", None)
    assert exc.value.figure_name == "Mystery Spin"
