from pathlib import Path

import pytest

MB50 = 50 * 1024 * 1024
SAMPLE = Path(__file__).resolve().parents[2] / "data" / "U12_figures_detail.pdf"


@pytest.fixture(autouse=True)
def inbox(tmp_path, monkeypatch):
    path = tmp_path / "inbox"
    monkeypatch.setenv("AQUABELY_INBOX", str(path))
    return path


@pytest.fixture
def sample_pdf_bytes():
    if not SAMPLE.exists():
        pytest.skip(f"sample PDF {SAMPLE} not available")
    return SAMPLE.read_bytes()


def _upload(client, data, name="u12.pdf"):
    return client.post("/api/imports/preview", files={"file": (name, data, "application/pdf")})


def test_preview_detects_format_for_a_sample_pdf(client, sample_pdf_bytes, inbox):
    r = _upload(client, sample_pdf_bytes)
    assert r.status_code == 200
    body = r.json()
    assert body["format_id"] == "u12"
    assert "u12" in body["available_formats"]
    assert body["filename"] == "u12.pdf"
    assert body["athlete_count"] > 0
    assert len(body["sha256"]) == 64
    assert (inbox / f"{body['sha256']}.pdf").exists()


def test_preview_unreadable_pdf_returns_null_format(client):
    r = _upload(client, b"not a pdf")
    assert r.status_code == 200
    body = r.json()
    assert body["format_id"] is None
    assert body["errors"]


def test_preview_rejects_oversize_upload(client, inbox):
    r = _upload(client, b"0" * (MB50 + 1), "big.pdf")
    assert r.status_code == 413
    assert r.json() == {"detail": "File exceeds 50 MB"}
    assert not inbox.exists() or not list(inbox.iterdir())


def test_preview_accepts_exactly_50_mb(client):
    r = _upload(client, b"0" * MB50, "edge.pdf")
    assert r.status_code != 413


def test_import_twice_returns_409(client, sample_pdf_bytes):
    preview = _upload(client, sample_pdf_bytes).json()
    body = {"sha256": preview["sha256"], "filename": preview["filename"],
            "format_id": preview["format_id"]}
    r = client.post("/api/imports", json=body)
    assert r.status_code == 201
    assert r.json()["athlete_count"] == preview["athlete_count"]
    assert r.json()["level"] == preview["level"]
    r2 = client.post("/api/imports", json=body)
    assert r2.status_code == 409
    assert r2.json() == {"detail": "Already imported"}


def test_import_unknown_upload_returns_404(client):
    body = {"sha256": "a" * 64, "filename": "x.pdf", "format_id": "u12"}
    r = client.post("/api/imports", json=body)
    assert r.status_code == 404
    assert r.json() == {"detail": "Upload not found"}


def test_import_validation_failure_returns_422_with_errors(client, sample_pdf_bytes, monkeypatch):
    from api.routers import imports
    from db.importer import ValidationFailed
    preview = _upload(client, sample_pdf_bytes).json()

    def boom(*a, **k):
        raise ValidationFailed(["bad total"])
    monkeypatch.setattr(imports, "import_competition", boom)
    body = {"sha256": preview["sha256"], "filename": "u12.pdf", "format_id": "u12"}
    r = client.post("/api/imports", json=body)
    assert r.status_code == 422
    assert r.json() == {"detail": "Validation failed", "errors": ["bad total"]}
