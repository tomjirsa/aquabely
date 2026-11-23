def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_unknown_api_path_is_json_404(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and r.headers["content-type"].startswith("application/json")


def test_non_api_path_without_dist_is_404(client, tmp_path, monkeypatch):
    import api.main
    monkeypatch.setattr(api.main, "DIST_DIR", tmp_path / "missing")
    assert client.get("/athletes/5").status_code == 404


def test_non_api_path_serves_app_shell(client, tmp_path, monkeypatch):
    import api.main
    (tmp_path / "index.html").write_text("<html>shell</html>")
    monkeypatch.setattr(api.main, "DIST_DIR", tmp_path)
    r = client.get("/athletes/5")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "shell" in r.text
