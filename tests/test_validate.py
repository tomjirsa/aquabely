from dataclasses import replace

from parser.models import FigureDef, FigureResult, ParsedCompetition, ParsedResult
from parser.validate import validate


def comp(judges=5, results=None, figures=None):
    figures = figures or [FigureDef("F1", "Ballet", 1.0)]
    results = results or [ParsedResult(1, 1, "A", "C", "CZE", 2016, 50.0, 0.0, 0.0,
                                       [FigureResult("F1", [5.0] * judges, 5.0, 0.0)])]
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
    bad = comp(figures=[FigureDef("F1", "Ballet", 1.0), FigureDef("F2", "Arch", 1.2)])
    assert any("figure" in e.lower() for e in validate(bad).errors)


def test_score_mismatch_is_a_warning_not_an_error():
    bad = comp()
    fr = bad.results[0].figure_results[0]
    bad.results[0].figure_results[0] = replace(fr, score=5.06)  # trimmed mean 5.0 x 1.0 = 5.0, off by more than 0.05
    rep = validate(bad)
    assert rep.errors == []
    assert any("score" in w.lower() for w in rep.warnings)


def test_trimmed_mean_within_tolerance_gives_no_warning():
    c = comp()
    # judges 3,5,5,5,9: plain mean 5.4, trimmed mean 5.0; score 5.04 is within 0.05
    c.results[0].figure_results[0] = FigureResult("F1", [3.0, 5.0, 5.0, 5.0, 9.0], 5.04, 0.0)
    assert validate(c).warnings == []
