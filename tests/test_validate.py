from dataclasses import replace

from parser.models import FigureDef, FigureResult, ParsedCompetition, ParsedResult
from parser.validate import validate


def comp(judges=5, results=None, figures=None):
    figures = figures or [FigureDef("F1", "Ballet Leg Single", 1.6, "101")]
    results = results or [ParsedResult(1, 1, "A", "C", "CZE", 2016, 50.0, 0.0, 0.0,
                                       [FigureResult("F1", [5.0] * judges, 8.0, 0.0)])]
    return ParsedCompetition("Cup", "2026-01-01", "", "L3", "2014–2019", 2014, 2019,
                             judges, figures, results)


def test_valid_competition_has_no_errors():
    rep = validate(comp())
    assert rep.errors == []


def test_wrong_judge_count_is_an_error():
    bad = comp(judges=5)
    bad.results[0].figure_results[0].judge_scores.pop()
    assert any("judge" in e.lower() for e in validate(bad).errors)


def test_missing_figure_row_is_an_error():
    bad = comp(figures=[FigureDef("F1", "Ballet Leg Single", 1.6, "101"), FigureDef("F2", "Kipnus", 1.4, "316")])
    assert any("figure" in e.lower() for e in validate(bad).errors)


def test_score_mismatch_is_a_warning_not_an_error():
    bad = comp()
    fr = bad.results[0].figure_results[0]
    bad.results[0].figure_results[0] = replace(fr, score=8.06)  # trimmed mean 5.0 x 1.6 = 8.0, off by more than 0.05
    rep = validate(bad)
    assert rep.errors == []
    assert any("score" in w.lower() for w in rep.warnings)


def test_trimmed_mean_within_tolerance_gives_no_warning():
    c = comp()
    # judges 3,5,5,5,9: plain mean 5.4, trimmed mean 5.0; score 8.04 is within 0.05
    c.results[0].figure_results[0] = FigureResult("F1", [3.0, 5.0, 5.0, 5.0, 9.0], 8.04, 0.0)
    assert validate(c).warnings == []


def _comp_with_figure(name, code, level, marks=None, score=0.0, judges=5):
    marks = marks if marks is not None else [5.0] * judges
    figures = [FigureDef("F1", name, None, code)]
    results = [ParsedResult(1, 1, "A", "C", "CZE", 2016, score, 0.0, 0.0,
                            [FigureResult("F1", marks, score, 0.0)])]
    return ParsedCompetition("Cup", "2026-01-01", "", level, "2014–2019", 2014, 2019,
                             judges, figures, results)


def test_unmatched_figure_is_an_error():
    c = _comp_with_figure(name="Mystery Spin", code=None, level="L3")
    rep = validate(c)
    assert any("unknown figure: Mystery Spin" in e for e in rep.errors)
    assert rep.warnings == []


def test_u12_score_is_checked_with_catalogue_coefficient():
    # Straight Ballet Leg 106 has coefficient 1.6; a mean of 5.0 gives 8.0
    c = _comp_with_figure(name="Straight Ballet Leg", code="106", level="U12", marks=[5.0] * 5, score=8.0)
    assert validate(c).warnings == []
    bad = _comp_with_figure(name="Straight Ballet Leg", code="106", level="U12", marks=[5.0] * 5, score=5.0)
    assert any("Straight Ballet Leg" in w for w in validate(bad).warnings)
