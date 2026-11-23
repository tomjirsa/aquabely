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


def test_built_asset_is_served_not_the_shell(client, tmp_path, monkeypatch):
    import api.main
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>shell</html>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path / "secret.txt").write_text("x")
    monkeypatch.setattr(api.main, "DIST_DIR", tmp_path / "assets")
    (tmp_path / "assets" / "index.html").write_text("<html>shell</html>")
    assert client.get("/app.js").text == "console.log(1)"
    assert "shell" in client.get("/../secret.txt").text
    assert "shell" in client.get("/%2e%2e/secret.txt").text


def _dist(tmp_path):
    """A built app in tmp_path/dist with a secret file beside it."""
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>shell</html>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path / "secret.txt").write_text("top secret")
    return dist


def _body(resp) -> str:
    """Body of a handler return value, read without going through httpx."""
    from fastapi.responses import FileResponse
    if isinstance(resp, FileResponse):
        from pathlib import Path
        return Path(resp.path).read_text()
    return resp.body.decode()


def test_missing_asset_is_404_not_the_shell(client, tmp_path, monkeypatch):
    import api.main
    monkeypatch.setattr(api.main, "DIST_DIR", _dist(tmp_path))
    r = client.get("/assets/missing-abc123.js")
    assert r.status_code == 404
    assert "shell" not in r.text
    assert client.get("/assets/app.js").text == "console.log(1)"


def test_app_shell_is_served_with_no_cache(client, tmp_path, monkeypatch):
    import api.main
    monkeypatch.setattr(api.main, "DIST_DIR", _dist(tmp_path))
    for path in ("/", "/athletes/5", "/index.html"):
        r = client.get(path)
        assert r.status_code == 200
        assert "shell" in r.text
        assert r.headers["cache-control"] == "no-cache", path


def test_traversal_passed_to_handler_does_not_return_the_file(tmp_path, monkeypatch):
    import api.main
    from fastapi import HTTPException
    monkeypatch.setattr(api.main, "DIST_DIR", _dist(tmp_path))
    for raw in ("../secret.txt", "assets/../../secret.txt", r"..\secret.txt",
                str(tmp_path / "secret.txt")):
        try:
            body = _body(api.main.spa_fallback(raw))
        except HTTPException as exc:
            assert exc.status_code == 404
            continue
        assert "top secret" not in body, raw


def test_null_byte_in_path_is_not_a_server_error(client, tmp_path, monkeypatch):
    import api.main
    from fastapi import HTTPException
    monkeypatch.setattr(api.main, "DIST_DIR", _dist(tmp_path))
    assert "shell" in _body(api.main.spa_fallback("athletes\x00x"))
    try:
        api.main.spa_fallback("assets/a\x00.js")
        raise AssertionError("expected 404")
    except HTTPException as exc:
        assert exc.status_code == 404
    r = client.get("/athletes%00x")
    assert r.status_code in (200, 404)
