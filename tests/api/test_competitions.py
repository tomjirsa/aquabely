import pytest


def test_results_include_birth_year_and_nulls(seeded_client, seeded_cc_id):
    rows = seeded_client.get(f"/api/competitions/{seeded_cc_id}/results").json()
    assert rows and "year_of_birth" in rows[0]
    assert "NaN" not in seeded_client.get(f"/api/competitions/{seeded_cc_id}/results").text


def test_figure_detail_marks_dropped_extremes(seeded_client, seeded_cc_id):
    rows = seeded_client.get(f"/api/competitions/{seeded_cc_id}/figure-detail").json()
    r = next(r for r in rows if r["judges"] and any(r["dropped"]))
    kept = [j for j, d in zip(r["judges"], r["dropped"]) if j is not None and not d]
    assert r["average"] == pytest.approx(sum(kept) / len(kept))


def test_unknown_competition_is_404(seeded_client):
    assert seeded_client.get("/api/competitions/99999/results").status_code == 404
    assert seeded_client.get("/api/competitions/99999/figures").status_code == 404
    assert seeded_client.get("/api/competitions/99999/figure-detail").status_code == 404


def test_list_and_figures(seeded_client, seeded_cc_id):
    comps = seeded_client.get("/api/competitions?level=U12").json()
    assert comps[0]["competition_category_id"] == seeded_cc_id
    assert set(comps[0]) == {"competition_category_id", "competition", "date", "age_group_label"}
    figs = seeded_client.get(f"/api/competitions/{seeded_cc_id}/figures").json()
    assert set(figs[0]) == {"number", "name", "difficulty"}
