def test_home_summary(seeded_client):
    body = seeded_client.get("/api/home?level=U12").json()
    assert body["athlete_count"] == 1
    assert body["top_scorer_name"] == "Ann"
    assert body["top_scorer_total"] == 50.0
    assert body["latest_competition"]["competition"] == "Cup"


def test_home_empty_level(seeded_client):
    body = seeded_client.get("/api/home?level=L3").json()
    assert body["athlete_count"] == 0
    assert body["latest_competition"] is None
    assert body["top_scorer_name"] is None
