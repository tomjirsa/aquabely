"""U12 ("AGE GROUP 12 AND UNDER") figure detail parser.

Layout of the sample (``data/U12_figures_detail.pdf``):

- Header: competition name, ``Location / dd.mm.yyyy``, the
  ``FIGURE DETAILED SCORES - AGE GROUP 12 AND UNDER`` title, the referee,
  four judge panels (``Judge N: : SURNAME Given``, one panel per figure)
  and the figures as ``Figures N:ID - Name`` (numeric ID, no difficulty).
- One block of four lines per athlete::

      1 <club> <NAME Given> (2014) Fig.1 7,2 7,5 7,8 7,8 7,8 12,3200 71,7956 [points behind]
      Fig.2 7,4 7,4 7,1 7,7 6,2 13,1400
      Fig.3 ...
      Fig.4 ...

  Each ``Fig.N`` line carries one mark per judge, then the figure score;
  ``Fig.1`` also carries the total and, below rank 1, the points behind.
  Decimal separator is a comma.

Club / name split rule
----------------------
The club sits in the NOC column (x ~ 60 pt) and the name in the name column
(x ~ 151 pt). Long clubs overflow into the name column and are overprinted
by the name, so the plain text line interleaves the two
(``Plzeň Fz.RsI.SCHOVÁ Tereza`` = club ``... Plzeň z.s.`` + name
``FRISCHOVÁ Tereza``). The text line cannot be split by words.

The PDF draws each cell as its own text run, in order: rank, club, name with
birth year. So the rule is: take the row line's characters left of the
``Fig.1`` label **in content-stream order** (``page.chars``, not sorted by x)
and start a new run whenever the next character begins left of the previous
character's right edge (a jump back: overprinted cell) or more than
``_RUN_GAP`` pt to its right (a jump forward across an empty column gap).
Every row must give exactly three runs: rank, club, ``NAME Given (YYYY)``.
Any other count raises ``ValueError``. All 76 sample rows split this way.

Names and clubs are stored exactly as extracted (no case or diacritic
changes).
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from parser.models import FigureDef, FigureResult, ParsedCompetition, ParsedResult

# Max forward gap (pt) between two characters of the same text run. Word
# spaces are drawn as characters, so in-run gaps are ~0; column gaps are >10.
_RUN_GAP = 3.0
# Characters whose top differs by less than this belong to the same line.
_LINE_TOL = 1.0

_SIGNATURE = "AGE GROUP 12 AND UNDER"
_PLACE_DATE = re.compile(r"^(.*?)\s*/\s*(\d{2})\.(\d{2})\.(\d{4})\s*$")
_JUDGE = re.compile(r"Judge\s+(\d+):")
_FIGURE = re.compile(r"Figures\s+(\d+):(\d+)\s*-\s*(.+?)\s*$")
_FIG_LINE = re.compile(r"(?:^|\s)Fig\.(\d+)\s+(.*)$")
_NUMBER = re.compile(r"^\d+(?:,\d+)?$")
_NAME_YOB = re.compile(r"^(.*?)\s*\((\d{4})\)$")


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def _split_runs(chars: list[dict]) -> list[str]:
    """Split characters (in content-stream order) into text runs.

    A run breaks when a character starts left of the previous one's right edge
    or more than ``_RUN_GAP`` to the right of it. Blank runs are dropped.
    """
    runs: list[list[str]] = []
    prev = None
    for c in chars:
        if prev is None or c["x0"] < prev["x1"] - _LINE_TOL or c["x0"] - prev["x1"] > _RUN_GAP:
            runs.append([])
        runs[-1].append(c["text"])
        prev = c
    texts = ("".join(r).strip() for r in runs)
    return [t for t in texts if t]


def _parse_header(lines: list[str]):
    """Name, ISO date, location, judges per panel and figures from page 1."""
    header: list[str] = []
    for ln in lines:
        if ln.strip().startswith("Judges Calculation"):
            break
        header.append(ln.strip())

    name = header[0] if header else ""
    date = location = ""
    for ln in header:
        m = _PLACE_DATE.match(ln)
        if m:
            location = m.group(1).strip()
            date = f"{m.group(4)}-{m.group(3)}-{m.group(2)}"
            break

    judge_numbers = [int(n) for ln in header for n in _JUDGE.findall(ln)]
    judges = max(judge_numbers, default=0)

    figures: dict[int, FigureDef] = {}
    for ln in header:
        m = _FIGURE.search(ln)
        if m:
            idx = int(m.group(1))
            figures[idx] = FigureDef(number=f"F{idx}", name=m.group(3), difficulty=None)
    return name, date, location, judges, [figures[k] for k in sorted(figures)]


def _row_identity(page, line: dict, fig1_words: list[dict]) -> tuple[int, str, str, int]:
    """Rank, club, name and birth year from a Fig.1 row, via the split rule."""
    fig_x0 = next(w["x0"] for w in fig1_words if abs(w["top"] - line["top"]) < _LINE_TOL)
    chars = [
        c for c in page.chars
        if abs(c["top"] - line["top"]) < _LINE_TOL and c["x1"] <= fig_x0
    ]
    runs = _split_runs(chars)
    if len(runs) != 3 or not runs[0].isdigit():
        raise ValueError(f"U12 row does not split into rank/club/name: {runs!r}")
    m = _NAME_YOB.match(runs[2])
    if not m:
        raise ValueError(f"U12 name run has no (YYYY) birth year: {runs[2]!r}")
    return int(runs[0]), runs[1], m.group(1), int(m.group(2))


def _parse_page(page, judges: int) -> list[dict]:
    rows: list[dict] = []
    fig1_words = [w for w in page.extract_words() if w["text"] == "Fig.1"]
    for line in page.extract_text_lines():
        fm = _FIG_LINE.search(line["text"])
        if not fm:
            continue
        fig = int(fm.group(1))
        tokens = fm.group(2).split()
        if not all(_NUMBER.match(t) for t in tokens):
            raise ValueError(f"U12 figure line has non-numeric data: {line['text']!r}")

        if fig == 1:
            if len(tokens) not in (judges + 2, judges + 3):
                raise ValueError(f"U12 Fig.1 line has {len(tokens)} numbers: {line['text']!r}")
            rank, club, name, yob = _row_identity(page, line, fig1_words)
            rows.append({
                "rank": rank, "club": club, "name": name, "yob": yob,
                "total": _num(tokens[judges + 1]),
                "behind": _num(tokens[judges + 2]) if len(tokens) == judges + 3 else 0.0,
                "figures": [],
            })
        else:
            if not rows:
                raise ValueError(f"U12 Fig.{fig} line before any athlete row: {line['text']!r}")
            if len(tokens) != judges + 1:
                raise ValueError(f"U12 Fig.{fig} line has {len(tokens)} numbers: {line['text']!r}")

        rows[-1]["figures"].append(FigureResult(
            figure_number=f"F{fig}",
            judge_scores=[_num(t) for t in tokens[:judges]],
            score=_num(tokens[judges]),
            penalty=0.0,
        ))
    return rows


class U12Parser:
    format_id = "u12"
    level_code = "U12"

    def detect(self, first_page_text: str) -> bool:
        return _SIGNATURE in first_page_text.upper()

    def parse(self, pdf_path: Path) -> ParsedCompetition:
        with pdfplumber.open(pdf_path) as pdf:
            first_lines = (pdf.pages[0].extract_text() or "").splitlines()
            name, date, location, judges, figures = _parse_header(first_lines)
            if judges == 0:
                raise ValueError("U12 header lists no judges")
            rows = [row for page in pdf.pages for row in _parse_page(page, judges)]

        results = [
            ParsedResult(
                rank=r["rank"],
                entry_number=None,
                name=r["name"],
                club=r["club"],
                country="",
                year_of_birth=r["yob"],
                total_score=r["total"],
                penalty=0.0,
                points_behind=r["behind"],
                figure_results=r["figures"],
            )
            for r in rows
        ]
        return ParsedCompetition(
            name=name,
            date=date,
            location=location,
            level_code=self.level_code,
            age_group_label="12 and under",
            birth_year_from=None,
            birth_year_to=None,
            judges_per_figure=judges,
            figures=figures,
            results=results,
        )


parser = U12Parser()
