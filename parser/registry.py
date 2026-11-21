from __future__ import annotations

from parser.formats.base import FormatParser
from parser.formats.l3 import L3Parser
from parser.formats.u12 import U12Parser


class UnknownFormatError(Exception):
    """No registered parser recognises the document."""


class AmbiguousFormatError(Exception):
    """More than one registered parser recognises the document."""


PARSERS: list[FormatParser] = [L3Parser(), U12Parser()]


def detect_format(first_page_text: str) -> FormatParser:
    matches = [p for p in PARSERS if p.detect(first_page_text)]
    if not matches:
        raise UnknownFormatError("No parser recognises this document")
    if len(matches) > 1:
        ids = ", ".join(p.format_id for p in matches)
        raise AmbiguousFormatError(f"Multiple parsers match: {ids}")
    return matches[0]


def get_parser(format_id: str) -> FormatParser:
    for p in PARSERS:
        if p.format_id == format_id:
            return p
    raise UnknownFormatError(f"Unknown format id: {format_id}")
