def test_clubs_list(seeded_client, seeded_club_id):
    rows = seeded_client.get("/api/clubs").json()
    assert rows and all(set(r) == {"id", "name"} for r in rows)
    assert seeded_club_id in [r["id"] for r in rows]


def test_club_detail_has_roster_and_medals(seeded_client, seeded_club_id):
    body = seeded_client.get(f"/api/clubs/{seeded_club_id}").json()
    assert set(body) >= {"name", "roster", "medals", "avg_scores"}
    assert body["roster"]
    assert all(set(m) == {"place", "count"} for m in body["medals"])
    assert all(set(a) == {"competition", "date", "avg_total"} for a in body["avg_scores"])


def test_unknown_club_is_404(seeded_client):
    resp = seeded_client.get("/api/clubs/99999")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Club not found"}
