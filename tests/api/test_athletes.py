import pytest
from fastapi.testclient import TestClient


def _athlete_id(client, q="Ann"):
    return client.get(f"/api/athletes?q={q}").json()[0]["id"]


def _set_marks(marks):
    from db.database import get_connection
    conn = get_connection()
    try:
        fr_id = conn.execute("SELECT MIN(id) FROM figure_results").fetchone()[0]
        conn.execute(
            "UPDATE figure_results SET judge_1=?, judge_2=?, judge_3=?, judge_4=?, "
            "judge_5=?, judge_6=?, judge_7=? WHERE id = ?", (*marks, fr_id))
        conn.commit()
    finally:
        conn.close()


def test_athlete_without_figure_detail_still_lists_competitions(athlete_without_figures_id):
    from api.main import app
    client = TestClient(app)
    rows = client.get(f"/api/athletes/{athlete_without_figures_id}/competitions").json()
    assert rows and rows[0]["figures"] == []
    assert rows[0]["rank_overall"] == 1
    assert client.get(f"/api/athletes/{athlete_without_figures_id}/figures").json() == []
    assert client.get(f"/api/athletes/{athlete_without_figures_id}").status_code == 200


def test_athlete_list_search_is_case_insensitive(seeded_client):
    rows = seeded_client.get("/api/athletes?q=ANN").json()
    assert rows and all("ann" in (r["name"] + r["club"]).lower() for r in rows)
    assert seeded_client.get("/api/athletes?q=zzzz").json() == []
    assert len(seeded_client.get("/api/athletes").json()) >= 1


def test_athlete_list_fields_and_no_nan(seeded_client):
    resp = seeded_client.get("/api/athletes")
    assert "NaN" not in resp.text
    assert set(resp.json()[0]) == {"id", "name", "club", "year_of_birth", "competitions",
                                   "best_score", "avg_score"}


def test_profile_has_history_and_overall_ranks(seeded_client):
    aid = _athlete_id(seeded_client)
    p = seeded_client.get(f"/api/athletes/{aid}").json()
    assert p["id"] == aid and p["competitions"] == 1
    assert p["history"] and "result_id" not in p["history"][0]
    assert "competition_category_id" not in p["history"][0]
    assert p["overall_ranks"][0]["rank_overall"] == 1


def test_competitions_merge_figure_ranks_and_dropped(seeded_client):
    _set_marks([6.5, 7.0, 5.0, 8.5, 7.5, 6.0, None])
    aid = _athlete_id(seeded_client)
    rows = seeded_client.get(f"/api/athletes/{aid}/competitions").json()
    assert len(rows) == 1 and rows[0]["rank_overall"] == 1
    fig = rows[0]["figures"][0]
    assert fig["fig_rank_overall"] == 1 and fig["fig_field_size"] == 1
    assert fig["judges"] == [6.5, 7.0, 5.0, 8.5, 7.5, 6.0, None]
    flagged = sorted(j for j, d in zip(fig["judges"], fig["dropped"]) if d)
    assert flagged == [5.0, 8.5]
    kept = [6.5, 7.0, 7.5, 6.0]
    assert fig["average"] == pytest.approx(sum(kept) / 4)


def test_figures_history_points(seeded_client):
    _set_marks([6.5, 7.0, 5.0, 8.5, 7.5, 6.0, None])
    aid = _athlete_id(seeded_client)
    hist = seeded_client.get(f"/api/athletes/{aid}/figures").json()
    assert hist and set(hist[0]) == {"figure_name", "points"}
    pt = next(p for h in hist for p in h["points"] if p["judges"][0] == 6.5)
    flagged = sorted(j for j, d in zip(pt["judges"], pt["dropped"]) if d)
    assert flagged == [5.0, 8.5]
    assert "NaN" not in seeded_client.get(f"/api/athletes/{aid}/figures").text


def test_unknown_athlete_is_404(seeded_client):
    for suffix in ("", "/competitions", "/figures"):
        resp = seeded_client.get(f"/api/athletes/99999{suffix}")
        assert resp.status_code == 404
        assert resp.json() == {"detail": "Athlete not found"}
