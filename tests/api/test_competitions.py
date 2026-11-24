import pytest


def test_results_include_birth_year_and_nulls(seeded_client, seeded_cc_id):
    rows = seeded_client.get(f"/api/competitions/{seeded_cc_id}/results").json()
    assert rows and "year_of_birth" in rows[0]
    assert "NaN" not in seeded_client.get(f"/api/competitions/{seeded_cc_id}/results").text


def test_figure_detail_marks_dropped_extremes(seeded_client, seeded_cc_id):
    # Seeded marks are all equal (5.0), which would make the check vacuous, so
    # give the first figure row distinct marks (one judge left null).
    from db.database import get_connection
    conn = get_connection()
    try:
        fr_id = conn.execute("SELECT MIN(id) FROM figure_results").fetchone()[0]
        conn.execute(
            "UPDATE figure_results SET judge_1=6.5, judge_2=7.0, judge_3=5.0, judge_4=8.5, "
            "judge_5=7.5, judge_6=6.0, judge_7=NULL WHERE id = ?", (fr_id,))
        conn.commit()
    finally:
        conn.close()

    rows = seeded_client.get(f"/api/competitions/{seeded_cc_id}/figure-detail").json()
    r = next(r for r in rows if r["judges"] == [6.5, 7.0, 5.0, 8.5, 7.5, 6.0, None])
    assert sum(r["dropped"]) == 2
    present = [j for j in r["judges"] if j is not None]
    flagged = sorted(j for j, d in zip(r["judges"], r["dropped"]) if d)
    assert flagged == [min(present), max(present)]
    kept = [j for j, d in zip(r["judges"], r["dropped"]) if j is not None and not d]
    assert r["average"] == pytest.approx(sum(kept) / len(kept))


def test_unknown_competition_is_404(seeded_client):
    for suffix in ("results", "figures", "figure-detail"):
        resp = seeded_client.get(f"/api/competitions/99999/{suffix}")
        assert resp.status_code == 404
        assert resp.json() == {"detail": "Competition not found"}


def test_known_competition_is_200(seeded_client, seeded_cc_id):
    for suffix in ("results", "figures", "figure-detail"):
        resp = seeded_client.get(f"/api/competitions/{seeded_cc_id}/{suffix}")
        assert resp.status_code == 200


def test_list_and_figures(seeded_client, seeded_cc_id):
    comps = seeded_client.get("/api/competitions?level=U12").json()
    assert comps[0]["competition_category_id"] == seeded_cc_id
    assert set(comps[0]) == {"competition_category_id", "competition", "date", "age_group_label"}
    figs = seeded_client.get(f"/api/competitions/{seeded_cc_id}/figures").json()
    assert set(figs[0]) == {"number", "name", "difficulty"}
