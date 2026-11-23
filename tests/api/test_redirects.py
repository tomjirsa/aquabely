def test_old_streamlit_paths_redirect(client):
    for old, new in [("/Import", "/import"), ("/Competitions", "/competitions"),
                     ("/Athletes", "/athletes"), ("/Clubs", "/clubs"), ("/Figures", "/figures")]:
        r = client.get(old, follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"] == new
