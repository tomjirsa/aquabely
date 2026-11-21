from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["views/0_home.py", "views/2_competitions.py", "views/3_athletes.py", "views/4_clubs.py"]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_on_empty_database(page, tmp_path, monkeypatch):
    monkeypatch.setenv("AQUABELY_DB", str(tmp_path / "t.db"))
    # DB_PATH is read at import time; another test may have imported db.database already.
    import db.database
    monkeypatch.setattr(db.database, "DB_PATH", tmp_path / "t.db")
    at = AppTest.from_file(str(ROOT / page), default_timeout=20).run()
    assert not at.exception


def test_athletes_page_renders_figure_detail_with_seeded_data(seeded_app_db):
    at = AppTest.from_file(str(ROOT / "views/3_athletes.py"), default_timeout=30).run()
    assert not at.exception
    assert any("Figure detail" in h.value for h in at.subheader)


def test_athletes_page_renders_selectable_figure_table(seeded_app_db):
    at = AppTest.from_file(str(ROOT / "views/3_athletes.py"), default_timeout=30).run()
    assert not at.exception
    assert any("Select a figure to see its judge marks." in c.value for c in at.caption)


def test_figures_page_renders_on_empty_database(tmp_path, monkeypatch):
    monkeypatch.setenv("AQUABELY_DB", str(tmp_path / "f.db"))
    import db.database
    monkeypatch.setattr(db.database, "DB_PATH", tmp_path / "f.db")
    at = AppTest.from_file(str(ROOT / "views/5_figures.py"), default_timeout=20).run()
    assert not at.exception


def test_figures_page_content_with_seeded_data(seeded_app_db):
    at = AppTest.from_file(str(ROOT / "views/5_figures.py"), default_timeout=30).run()
    assert not at.exception
    assert list(at.radio[0].options) == ["L3", "U12"]
    df = at.dataframe[0].value
    assert len(df) == 4
    assert "101" in set(df["code"].astype(str))
    for col in ["code", "name", "coefficient", "description_cs", "performances", "competitions"]:
        assert col in df.columns
    assert any("No performances recorded" in i.value for i in at.info)

    at.radio[0].set_value("U12").run()
    assert not at.exception
    df = at.dataframe[0].value
    assert len(df) == 8
    assert "106" in set(df["code"].astype(str))


def test_figures_page_registered_between_competitions_and_athletes():
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    titles = ["Competitions", "Figures", "Athletes"]
    positions = [text.find(f'title="{t}"') for t in titles]
    assert all(p >= 0 for p in positions)
    assert positions == sorted(positions)
    assert 'st.Page("views/5_figures.py", title="Figures"' in text


def test_competitions_page_figure_detail_renders_with_seeded_data(seeded_app_db):
    at = AppTest.from_file(str(ROOT / "views/2_competitions.py"), default_timeout=30).run()
    assert not at.exception


def test_athletes_page_has_one_tab_per_competition(seeded_app_db):
    at = AppTest.from_file(str(ROOT / "views/3_athletes.py"), default_timeout=30).run()
    assert not at.exception
    from db.database import get_connection
    from db.queries import athlete_rankings
    conn = get_connection()
    aid = int(at.selectbox[0].value)
    comps = set(athlete_rankings(conn, aid)["competition"])
    conn.close()
    assert comps
    labels = [t.label for t in at.tabs]
    for comp in comps:
        assert any(comp in lbl for lbl in labels)


def test_athletes_page_renders_styled_figure_tables(seeded_app_db):
    at = AppTest.from_file(str(ROOT / "views/3_athletes.py"), default_timeout=30).run()
    assert not at.exception
    assert any("aq-tbl-row" in m.value for m in at.markdown)
