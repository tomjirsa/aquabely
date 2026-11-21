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


def test_figures_page_renders_on_empty_database(tmp_path, monkeypatch):
    monkeypatch.setenv("AQUABELY_DB", str(tmp_path / "f.db"))
    import db.database
    monkeypatch.setattr(db.database, "DB_PATH", tmp_path / "f.db")
    at = AppTest.from_file(str(ROOT / "views/5_figures.py"), default_timeout=20).run()
    assert not at.exception
