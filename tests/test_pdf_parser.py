from pathlib import Path
import pytest
from parser.pdf_parser import parse_pdf, file_sha256

SAMPLE = Path.home() / "Downloads" / "result_detail_Beginner L3 FIG (2019-2014).pdf"

pytestmark = pytest.mark.skipif(not SAMPLE.exists(), reason="sample PDF not found")


def test_competition_name():
    r = parse_pdf(SAMPLE)
    assert r.competition_name == "Delfinek cup"


def test_date():
    r = parse_pdf(SAMPLE)
    assert r.date == "16.05.2026"


def test_category_name():
    r = parse_pdf(SAMPLE)
    assert "Beginner L3 FIG" in r.category_name


def test_figures_count():
    r = parse_pdf(SAMPLE)
    assert len(r.figures) == 4


def test_first_figure():
    r = parse_pdf(SAMPLE)
    f = r.figures[0]
    assert f.number == "F1"
    assert "Ballet Leg" in f.name
    assert f.difficulty == 1.6


def test_result_count():
    r = parse_pdf(SAMPLE)
    assert len(r.results) == 43


def test_first_athlete_identity():
    r = parse_pdf(SAMPLE)
    a = r.results[0]
    assert a.rank == 1
    assert a.name == "Chromíková Sára"
    assert a.club == "Delfínek Ostrava"
    assert a.country == "CZE"
    assert a.yob == 2016
    assert a.entry_number == 34


def test_first_athlete_score():
    r = parse_pdf(SAMPLE)
    assert abs(r.results[0].total_score - 60.5636) < 0.01


def test_first_athlete_figure_results():
    r = parse_pdf(SAMPLE)
    frs = r.results[0].figure_results
    assert len(frs) == 4
    assert abs(frs[0].score - 9.9440) < 0.01
    assert frs[0].figure_number == "F1"
    assert len(frs[0].judge_scores) == 7


def test_points_behind_first_place():
    r = parse_pdf(SAMPLE)
    assert r.results[0].points_behind == 0.0


def test_points_behind_second_place():
    r = parse_pdf(SAMPLE)
    assert abs(r.results[1].points_behind - 2.74) < 0.01


def test_sha256_stable():
    h1 = file_sha256(SAMPLE)
    h2 = file_sha256(SAMPLE)
    assert h1 == h2
    assert len(h1) == 64
