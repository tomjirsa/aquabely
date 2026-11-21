from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["pages/0_home.py", "pages/2_competitions.py", "pages/3_athletes.py", "pages/4_clubs.py"]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_on_empty_database(page, tmp_path, monkeypatch):
    monkeypatch.setenv("AQUABELY_DB", str(tmp_path / "t.db"))
    at = AppTest.from_file(str(ROOT / page), default_timeout=20).run()
    assert not at.exception
