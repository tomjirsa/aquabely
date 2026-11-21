from pathlib import Path
import pytest
from parser.formats.u12 import U12Parser, _split_runs
from parser.text import normalize_club, normalize_person_name

SAMPLE = Path(__file__).parent.parent / "data" / "U12_figures_detail.pdf"
needs_sample = pytest.mark.skipif(not SAMPLE.exists(), reason="sample U12 PDF not in data/")


@pytest.fixture(scope="module")
def comp():
    return U12Parser().parse(SAMPLE)


@needs_sample
def test_u12_figures_have_no_difficulty_and_five_judges(comp):
    assert comp.level_code == "U12"
    assert comp.judges_per_figure == 5
    assert [f.difficulty for f in comp.figures] == [None, None, None, None]
    assert [f.number for f in comp.figures] == ["F1", "F2", "F3", "F4"]


@needs_sample
def test_u12_ranks_are_consecutive_and_every_athlete_has_four_figures(comp):
    assert [r.rank for r in comp.results] == list(range(1, len(comp.results) + 1))
    assert all(len(r.figure_results) == 4 for r in comp.results)
    assert all(len(fr.judge_scores) == 5 for r in comp.results for fr in r.figure_results)


@needs_sample
def test_first_u12_row_matches_the_pdf(comp):
    first = comp.results[0]
    assert first.year_of_birth == 2014
    assert first.figure_results[0].judge_scores == [7.2, 7.5, 7.8, 7.8, 7.8]
    assert first.total_score == pytest.approx(71.7956)


@needs_sample
def test_u12_header_fields(comp):
    assert comp.age_group_label == "12 and under"
    assert comp.birth_year_from is None
    assert comp.date == "2026-11-21"
    assert comp.location == "Brno"
    assert [f.name for f in comp.figures] == [
        "Ballet Leg Single", "Barracuda", "Front Ariana", "Tower"]
    assert len(comp.results) == 76


@needs_sample
def test_u12_scores_and_points_behind(comp):
    first, second, last = comp.results[0], comp.results[1], comp.results[-1]
    assert [fr.figure_number for fr in first.figure_results] == ["F1", "F2", "F3", "F4"]
    assert [fr.score for fr in first.figure_results] == pytest.approx(
        [12.32, 13.14, 14.96, 13.4267])
    assert first.points_behind == 0.0
    assert second.points_behind == pytest.approx(0.4312)
    assert last.rank == 76
    assert last.total_score == pytest.approx(42.84)
    assert last.points_behind == pytest.approx(28.9556)


# Club/name split. In the raw text line these rows are interleaved, e.g.
# rank 1 extracts as "Plzeň Fz.RsI.SCHOVÁ Tereza" and rank 6 as
# "klubV UUn iLvilelyrz (i2ta0 1B5rn)o".
@needs_sample
@pytest.mark.parametrize("rank, club, name", [
    (1, "Plavecký klub Slávia VŠ Plzeň z.s.", "FRISCHOVÁ Tereza"),       # club overprints name
    (2, "Spolek pro akvabely, z.s.", "RADKOVIČOVÁ Sofie"),               # no overlap
    (6, "Vysokoškolský sportovní klub Univerzita Brno", "VU Lilly"),     # club overflows past YoB
    (12, "Sport Club Plavecký areál Pardubice, z.s.", "VÍŠOVÁ Laura"),
    (47, "Sportovní Klub policie KOMETA BRNO z.s.", "ODEHNALOVÁ Emma Marie"),  # two given names
    (61, "TJ TESLA BRNO z.s.", "JELINKOVÁ Josefína Grace"),
])
def test_club_and_name_are_split(comp, rank, club, name):
    r = comp.results[rank - 1]
    assert (r.rank, r.club, r.name) == (rank, normalize_club(club), normalize_person_name(name))


@needs_sample
def test_no_name_or_club_carries_row_debris(comp):
    for r in comp.results:
        assert r.name and r.club
        assert "(" not in r.name and "Fig" not in r.name
        assert not any(ch.isdigit() for ch in r.name + r.club)


def _chars(*pieces):
    """Build fake pdfplumber chars: each piece is (x0, text), 4pt per char."""
    out = []
    for x0, text in pieces:
        for i, ch in enumerate(text):
            out.append({"text": ch, "x0": x0 + 4 * i, "x1": x0 + 4 * (i + 1)})
    return out


def test_split_runs_breaks_on_backward_jump_and_on_column_gap():
    # rank at 30, club at 60 overflowing to 100, name drawn later starting at 80
    chars = _chars((30, "1"), (60, "Club z.s."), (80, "NAME Given (2014)"))
    assert _split_runs(chars) == ["1", "Club z.s.", "NAME Given (2014)"]


def test_split_runs_keeps_contiguous_text_together():
    assert _split_runs(_chars((60, "Spolek pro akvabely"))) == ["Spolek pro akvabely"]


@needs_sample
def test_u12_names_are_normalised(comp):
    assert comp.results[0].name == "Frischová Tereza"
    assert comp.results[0].club == "Plavecký Klub Slávia VŠ Plzeň z.s."


@needs_sample
def test_u12_figure_names_have_no_numeric_id(comp):
    for f in comp.figures:
        assert not any(ch.isdigit() for ch in f.name), f.name
        assert not f.name.startswith(":")


def test_ballet_leg_variants_share_one_canonical_name():
    from parser.formats.l3 import normalize_figure_name
    assert normalize_figure_name("Straight Ballet Leg") == normalize_figure_name(
        "Ballet Leg Single") == "Ballet Leg Single"
