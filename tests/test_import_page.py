from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGE = str(Path(__file__).resolve().parent.parent / "pages" / "1_import.py")


def test_import_page_renders_without_exception(tmp_path, monkeypatch):
    monkeypatch.setenv("AQUABELY_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("AQUABELY_INBOX", str(tmp_path / "inbox"))
    at = AppTest.from_file(PAGE, default_timeout=20).run()
    assert not at.exception


def test_placeholder_required_when_detection_fails():
    from ui.import_helpers import format_options, needs_format_choice

    ids = ["a", "b"]
    assert needs_format_choice(None) is True
    assert needs_format_choice("a") is False
    assert format_options(ids, None) == [None, "a", "b"]
    assert format_options(ids, "b") == ["a", "b"]


def test_write_if_changed_skips_identical_bytes(tmp_path):
    from ui.import_helpers import write_if_changed

    f = tmp_path / "x.pdf"
    assert write_if_changed(f, b"one") is True
    assert write_if_changed(f, b"one") is False
    assert write_if_changed(f, b"two") is True
    assert f.read_bytes() == b"two"


def test_page_has_no_path_keyed_cache():
    src = (Path(PAGE)).read_text(encoding="utf-8")
    assert "cache_data" not in src and "cache_resource" not in src
