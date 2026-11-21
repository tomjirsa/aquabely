from pathlib import Path
import pytest
from parser.formats.l3 import L3Parser

DATA = Path(__file__).parent.parent / "data"
BEGINNER = DATA / "result_detail_Beginner L3 FIG (2019-2014).pdf"
HERSALKOVA = DATA / "result_detail_L3 FIG (2015-2019) Hersalkova.pdf"

needs_samples = pytest.mark.skipif(not BEGINNER.exists() or not HERSALKOVA.exists(),
                                   reason="sample L3 PDFs not in data/")


@needs_samples
def test_beginner_sample_keeps_all_seven_judges():
    comp = L3Parser().parse(BEGINNER)
    assert comp.level_code == "L3"
    assert comp.judges_per_figure == 7
    assert (comp.birth_year_from, comp.birth_year_to) == (2014, 2019)
    assert [(f.number, f.difficulty) for f in comp.figures] == [
        ("F1", 1.6), ("F2", 1.2), ("F3", 1.4), ("F4", 1.3)]
    assert len(comp.results) == 43
    f1 = comp.results[0].figure_results[0]
    assert f1.judge_scores == [6.1, 6.2, 6.4, 6.2, 6.2, 6.2, 6.2]
    assert f1.score == pytest.approx(9.944)


@needs_samples
def test_hersalkova_sample_has_five_judges():
    comp = L3Parser().parse(HERSALKOVA)
    assert comp.judges_per_figure == 5
    assert (comp.birth_year_from, comp.birth_year_to) == (2015, 2019)
    assert len(comp.results) == 43
    assert comp.results[0].entry_number == 14
    assert comp.results[0].figure_results[0].judge_scores == [4.8, 5.7, 5.1, 5.6, 5.5]


@needs_samples
def test_penalty_and_points_behind_for_winner():
    comp = L3Parser().parse(BEGINNER)
    assert comp.results[0].penalty == 0.0
    assert comp.results[0].points_behind == 0.0
