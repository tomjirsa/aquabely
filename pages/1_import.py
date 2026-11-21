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


@st.cache_data(show_spinner=False)
def _parse(path: str, format_id: str):
    return get_parser(format_id).parse(Path(path))


uploaded = st.file_uploader("Upload PDF", type="pdf", accept_multiple_files=True)

for uf in (uploaded or []):
    data = uf.getvalue()
    sha = _sha256(data)
    dest = INBOX / uf.name
    dest.write_bytes(data)

    st.subheader(uf.name)
    detected = None
    try:
        detected = detect_format(_first_page_text(dest)).format_id
    except (UnknownFormatError, AmbiguousFormatError) as exc:
        st.error(f"Could not detect the format: {exc}")
    except Exception as exc:
        st.error(f"Could not read the PDF: {exc}")
        continue

    index = format_ids.index(detected) if detected in format_ids else 0
    if detected:
        st.caption(f"Detected format: {detected}")
    format_id = st.selectbox("Format", format_ids, index=index, key=f"fmt_{sha}")
    if detected is None:
        st.warning("Pick the format manually to continue.")

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
