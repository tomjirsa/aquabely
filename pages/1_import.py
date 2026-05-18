from pathlib import Path

import streamlit as st

import db.database as database
from parser.pdf_parser import file_sha256, parse_pdf

INBOX = Path.home() / "aquabely_inbox"

st.title("Import Results")

database.init_schema()
INBOX.mkdir(exist_ok=True)

pdfs = sorted(INBOX.glob("*.pdf"))
if not pdfs:
    st.info(f"No PDFs found in {INBOX}. Drop result PDF files there to import them.")
    st.stop()

for pdf in pdfs:
    sha = file_sha256(pdf)
    already = database.is_imported(sha)
    col1, col2 = st.columns([4, 1])
    col1.write(f"{'✅' if already else '🔸'} `{pdf.name}`")
    if not already:
        if col2.button("Import", key=str(pdf)):
            with st.spinner(f"Parsing {pdf.name}…"):
                try:
                    parsed = parse_pdf(pdf)
                    database.insert_pdf_result(parsed, pdf.name, sha)
                    st.success(
                        f"Imported **{len(parsed.results)}** athletes — "
                        f"{parsed.competition_name} / {parsed.category_name}"
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed: {exc}")
