import hashlib
import os
from pathlib import Path

import pdfplumber
import streamlit as st

from db.database import get_connection, init_schema
from db.importer import DuplicateImportError, ValidationFailed, import_competition
from parser.registry import (PARSERS, AmbiguousFormatError, UnknownFormatError,
                             detect_format, get_parser)
from parser.validate import validate
from ui.import_helpers import (FORMAT_PLACEHOLDER, format_options,
                               needs_format_choice, upload_path,
                               write_if_changed)
from ui.theme import inject_theme

INBOX = Path(os.environ.get("AQUABELY_INBOX", Path(__file__).parent.parent / "data"))

inject_theme()
st.title("Import Results")

INBOX.mkdir(parents=True, exist_ok=True)
format_ids = [p.format_id for p in PARSERS]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _first_page_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return (pdf.pages[0].extract_text() or "") if pdf.pages else ""


def _parse(path: str, format_id: str):
    # Deliberately uncached: a cache keyed by path could serve a stale parse
    # for a different file uploaded under the same name.
    return get_parser(format_id).parse(Path(path))


uploaded = st.file_uploader("Upload PDF", type="pdf", accept_multiple_files=True)

for uf in (uploaded or []):
    data = uf.getvalue()
    sha = _sha256(data)
    dest = upload_path(INBOX, data)
    write_if_changed(dest, data)

    st.subheader(uf.name)
    detected = None
    try:
        detected = detect_format(_first_page_text(dest)).format_id
    except (UnknownFormatError, AmbiguousFormatError) as exc:
        st.error(f"Could not detect the format: {exc}")
    except Exception as exc:
        st.error(f"Could not read the PDF: {exc}")
        continue

    if detected:
        st.caption(f"Detected format: {detected}")
    options = format_options(format_ids, detected)
    index = options.index(detected) if detected in options else 0
    format_id = st.selectbox("Format", options, index=index, key=f"fmt_{sha}",
                             format_func=lambda v: FORMAT_PLACEHOLDER if v is None else v)
    if needs_format_choice(detected) and format_id is None:
        st.warning("Pick the format manually to continue.")
        st.button("Import", key=f"imp_{sha}", disabled=True)
        continue

    try:
        comp = _parse(str(dest), format_id)
    except Exception as exc:
        st.error(f"Parsing failed: {exc}")
        continue

    st.write(f"Level: **{comp.level_code}** | {comp.name} | {len(comp.results)} athletes")
    report = validate(comp)
    for e in report.errors:
        st.error(e)
    for w in report.warnings:
        st.warning(w)

    if st.button("Import", key=f"imp_{sha}", disabled=bool(report.errors)):
        conn = get_connection()
        try:
            init_schema(conn)
            import_competition(conn, comp, sha, uf.name)
            st.success(f"Imported {len(comp.results)} athletes ({comp.level_code}).")
        except DuplicateImportError:
            st.info("already imported")
        except ValidationFailed as exc:
            st.error("; ".join(exc.errors))
        except Exception as exc:
            st.error(f"Import failed: {exc}")
        finally:
            conn.close()
