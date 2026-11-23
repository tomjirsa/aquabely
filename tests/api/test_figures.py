import pytest


def test_figures_rejects_unknown_level(seeded_client):
    assert seeded_client.get("/api/figures?level=X").status_code == 422


def test_figures_requires_level(seeded_client):
    assert seeded_client.get("/api/figures").status_code == 422


@pytest.mark.parametrize("level", ["L3", "U12"])
def test_figures_catalogue_shape(seeded_client, level):
    resp = seeded_client.get(f"/api/figures?level={level}")
    assert resp.status_code == 200
    rows = resp.json()
    assert isinstance(rows, list)
    for row in rows:
        assert set(row) == {"code", "name", "coefficient", "description_cs",
                            "performances", "competitions"}
