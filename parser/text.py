"""Text normalisation shared by the PDF format parsers."""
from __future__ import annotations

import re


_DOTTED_ABBREV = re.compile(r"^(?:[a-z]{1,3}\.){2,}$")


def _collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _is_title(w: str) -> bool:
    """True when every hyphen-segment starts uppercase and continues lowercase."""
    return all(
        seg and seg[0].isupper() and seg[1:] == seg[1:].lower()
        for seg in w.split("-")
    )


def normalize_club(s: str) -> str:
    """Collapse whitespace and normalize casing word by word.

    - all-lowercase              -> capitalize        ("cup" -> "Cup")
    - ALL-CAPS up to 3 letters   -> keep              (abbreviations: FIG, SK, TJ, VŠ)
    - ALL-CAPS longer            -> capitalize        (TESLA -> Tesla, HOLUBCOVÁ -> Holubcová)
    - valid title / hyphen-title -> keep              (Chromíková, Nuler-Trageser)
    - broken mixed case          -> capitalize        (ChROMÍKOVÁ -> Chromíková)
    - lowercase dotted abbrev.   -> keep              (z.s., o.p.s.)
    """
    def _cap(w: str) -> str:
        if _DOTTED_ABBREV.match(w):
            return w  # legal-form abbreviations such as "z.s."
        if w == w.lower():
            return w.capitalize()
        if w == w.upper():
            return w if len(w) <= 3 else w.capitalize()
        if _is_title(w):
            return w
        return w.capitalize()

    return " ".join(_cap(w) for w in _collapse(s).split())


def normalize_person_name(s: str) -> str:
    """Collapse whitespace and capitalise each word of an athlete name.

    ALL-CAPS words (ASCII or not) are capitalised; valid title and
    hyphen-title words are kept; anything else is capitalised.
    """
    def _cap(w: str) -> str:
        if _is_title(w):
            return w
        if "-" in w:
            return "-".join(seg.capitalize() for seg in w.split("-"))
        return w.capitalize()

    return " ".join(_cap(w) for w in _collapse(s).split())
