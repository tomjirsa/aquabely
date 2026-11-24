from api.routers.imports import upload_path, write_if_changed


def test_write_if_changed_skips_identical_bytes(tmp_path):
    f = tmp_path / "x.pdf"
    assert write_if_changed(f, b"one") is True
    assert write_if_changed(f, b"one") is False
    assert write_if_changed(f, b"two") is True
    assert f.read_bytes() == b"two"


def test_upload_path_ignores_name_and_stays_in_inbox(tmp_path):
    data = b"%PDF-bytes"
    p = upload_path(tmp_path, data)
    assert p.parent == tmp_path
    assert p.suffix == ".pdf"
    assert upload_path(tmp_path, data) == p
    assert upload_path(tmp_path, b"other") != p
