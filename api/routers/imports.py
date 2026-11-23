import hashlib
import os
import re
from pathlib import Path

import pdfplumber
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from api.schemas import ImportPreview, ImportRequest, ImportResult
from db.database import get_connection, init_schema
from db.importer import DuplicateImportError, ValidationFailed, import_competition
from parser.registry import (PARSERS, AmbiguousFormatError, UnknownFormatError,
                             detect_format, get_parser)
from parser.validate import validate
from ui.import_helpers import upload_path, write_if_changed

router = APIRouter(prefix="/api/imports")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
CHUNK = 1024 * 1024


def _inbox() -> Path:
    default = Path(__file__).resolve().parent.parent.parent / "data"
    inbox = Path(os.environ.get("AQUABELY_INBOX", default))
    inbox.mkdir(parents=True, exist_ok=True)
    return inbox


def _too_large() -> HTTPException:
    return HTTPException(status_code=413, detail="File exceeds 50 MB")


def _first_page_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return (pdf.pages[0].extract_text() or "") if pdf.pages else ""


async def _read_capped(file: UploadFile) -> bytes:
    buf = bytearray()
    while True:
        chunk = await file.read(CHUNK)
        if not chunk:
            break
        buf += chunk
        if len(buf) > MAX_UPLOAD_BYTES:
            raise _too_large()
    return bytes(buf)


@router.post("/preview", response_model=ImportPreview)
async def preview(file: UploadFile):
    data = await _read_capped(file)
    sha = hashlib.sha256(data).hexdigest()
    dest = upload_path(_inbox(), data)
    write_if_changed(dest, data)

    result = {"sha256": sha, "filename": file.filename or "upload.pdf",
              "available_formats": [p.format_id for p in PARSERS],
              "errors": [], "warnings": []}
    try:
        result["format_id"] = detect_format(_first_page_text(dest)).format_id
    except (UnknownFormatError, AmbiguousFormatError) as exc:
        result["errors"].append(f"Could not detect the format: {exc}")
        return result
    except Exception as exc:
        result["errors"].append(f"Could not read the PDF: {exc}")
        return result

    try:
        comp = get_parser(result["format_id"]).parse(dest)
    except Exception as exc:
        result["errors"].append(f"Parsing failed: {exc}")
        return result
    report = validate(comp)
    result.update(level=comp.level_code, competition=comp.name,
                  athlete_count=len(comp.results),
                  errors=list(report.errors), warnings=list(report.warnings))
    return result


@router.post("", response_model=ImportResult, status_code=201)
def import_upload(body: ImportRequest):
    if not re.fullmatch(r"[0-9a-f]{64}", body.sha256):
        raise HTTPException(status_code=404, detail="Upload not found")
    path = _inbox() / f"{body.sha256}.pdf"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Upload not found")
    try:
        comp = get_parser(body.format_id).parse(path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Parsing failed: {exc}")
    conn = get_connection()
    try:
        init_schema(conn)
        import_competition(conn, comp, body.sha256, body.filename)
    except DuplicateImportError:
        return JSONResponse(status_code=409, content={"detail": "Already imported"})
    except ValidationFailed as exc:
        return JSONResponse(status_code=422,
                            content={"detail": "Validation failed", "errors": exc.errors})
    finally:
        conn.close()
    return ImportResult(athlete_count=len(comp.results), level=comp.level_code)
