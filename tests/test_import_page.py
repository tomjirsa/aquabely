from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGE = str(Path(__file__).resolve().parent.parent / "pages" / "1_import.py")


def test_import_page_renders_without_exception(tmp_path, monkeypatch):
    monkeypatch.setenv("AQUABELY_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("AQUABELY_INBOX", str(tmp_path / "inbox"))
    at = AppTest.from_file(PAGE, default_timeout=20).run()
    assert not at.exception
