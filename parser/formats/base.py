from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from parser.models import ParsedCompetition


@runtime_checkable
class FormatParser(Protocol):
    format_id: str
    level_code: str

    def detect(self, first_page_text: str) -> bool: ...

    def parse(self, pdf_path: Path) -> ParsedCompetition: ...
