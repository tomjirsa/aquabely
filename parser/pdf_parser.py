import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber


@dataclass
class FigureDef:
    number: str
    name: str
    difficulty: float


@dataclass
class FigureResult:
    figure_number: str
    judge_scores: list
    score: float
    penalty: float


@dataclass
class AthleteResult:
    rank: int
    entry_number: int
    name: str
    club: str
    country: str
    yob: int
    total_score: float
    penalty: float
    points_behind: float
    figure_results: list = field(default_factory=list)


@dataclass
class ParsedPDF:
    competition_name: str
    date: str
    category_name: str
    figures: list
    results: list


# Matches a figure score line anywhere in a text line:
# F1 6.10 6.20 6.40 6.20 6.20 6.20 6.20 9.9440 0.00
_FIG_SCORE = re.compile(
    r"(F\d+)\s+"
    r"([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"
    r"([\d.]+)\s+([\d.]+)"
)

# Rank/country/yob/total/points line: '1. CZE 2016 60.5636' or '2. CZE 2016 57.8236 2.7400'
# Total always has 4 decimal places; points_behind may be merged without space or have a space.
_RANK_LINE = re.compile(
    r"^(\d+)\.\s+(\w+)\s+(\d{4})\s+(\d+\.\d{4})\s*([\d.]+)?$"
)

# Entry/name line: '34 - Chromíková Sára F2 ...'
_ENTRY_NAME = re.compile(r"^(\d+)\s*-\s*(.*?)\s+F\d+\s")

# Club line (club name, then figure data): 'Delfínek Ostrava F3 ...'
_CLUB_LINE = re.compile(r"^(.*?)\s+F\d+\s")


def parse_pdf(path: Path) -> "ParsedPDF":
    all_lines: list[str] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_lines.extend(text.split("\n"))

    comp_name, date, category = _parse_header(all_lines)
    figures = _parse_figures(all_lines)
    results = _parse_results(all_lines, figures)

    return ParsedPDF(comp_name, date, category, figures, results)


def _parse_header(lines: list[str]):
    """Extract competition name, date, and category from the first page header."""
    # Filter out empty lines and known non-header lines
    clean = [ln.strip() for ln in lines if ln.strip()]
    clean = [
        ln for ln in clean
        if not re.match(r"^©", ln)
        and not ln.isdigit()
        and not ln.lower().startswith("rank country")
        and ln != "Points"
        and ln != "behind"
    ]

    comp_name = clean[0] if clean else "Unknown"
    date, category = "", ""

    if len(clean) > 1:
        # '16.05.2026 - - Beginner L3 FIG (2019-2014)'
        m = re.match(
            r"(\d{2}\.\d{2}\.\d{4})\s*-\s*-?\s*(.*)",
            clean[1],
        )
        if m:
            date = m.group(1)
            category = m.group(2).strip().strip("-").strip()

    return comp_name, date, category


def _parse_figures(lines: list[str]) -> list:
    """Parse figure definitions from the header area of page 1."""
    # Find lines before the data area (before first rank line)
    header_lines: list[str] = []
    for line in lines:
        if re.match(r"^\d+\.\s+\w{3}\s+\d{4}", line):
            break
        # Also stop at column header line
        if line.strip().lower().startswith("rank country"):
            break
        header_lines.append(line)

    figures: dict[str, tuple[str, float]] = {}

    for i, line in enumerate(header_lines):
        m = re.match(r"(F\d+):\s*(.*)", line)
        if not m:
            continue

        fig_num = m.group(1)
        rest = m.group(2)

        # A single line may contain multiple figure defs (e.g. 'F1: X (1.6) F3: Y (1.4)F4: Z (1.3)')
        # Split by the next F{n}: occurrences
        parts = re.split(r"(?=F\d+:)", rest)

        # First part belongs to fig_num
        first_part = parts[0].strip()
        dm = re.search(r"\((\d+\.\d+)\)", first_part)
        if dm:
            name = first_part[: dm.start()].strip()
            figures[fig_num] = (name, float(dm.group(1)))
        else:
            # Difficulty not on this line — scan forward, skipping other F{n}: lines
            name = first_part
            for j in range(i + 1, len(header_lines)):
                next_line = header_lines[j]
                if re.match(r"F\d+:", next_line):
                    continue  # belongs to a different figure
                dm2 = re.search(r"\((\d+\.\d+)\)", next_line)
                if dm2:
                    cont = next_line[: dm2.start()].strip()
                    if cont:
                        name = name + " " + cont
                    figures[fig_num] = (name.strip(), float(dm2.group(1)))
                    break

        # Handle additional figures packed onto same line (F3:, F4: after F1:)
        for p in parts[1:]:
            pm = re.match(r"(F\d+):\s*(.*)", p.strip())
            if pm:
                sub_fig = pm.group(1)
                sub_rest = pm.group(2)
                sdm = re.search(r"\((\d+\.\d+)\)", sub_rest)
                if sdm:
                    sub_name = sub_rest[: sdm.start()].strip()
                    figures[sub_fig] = (sub_name, float(sdm.group(1)))

    return [
        FigureDef(number=k, name=v[0], difficulty=v[1])
        for k, v in sorted(figures.items())
    ]


def _parse_results(lines: list[str], figures: list) -> list:
    """Parse athlete results from all text lines."""
    n_figures = len(figures) or 4

    # Collect all lines grouped by athlete.
    # Each athlete occupies exactly 5 lines in the text:
    #   line 0: 'F1 <scores>'
    #   line 1: '{entry} - {name} F2 <scores>'
    #   line 2: '{rank}. {country} {yob} {total} [{points}]'
    #   line 3: '{club} F3 <scores>'
    #   line 4: 'F4 <scores>'
    #
    # We identify athlete blocks by the rank line pattern.

    # First pass: find all rank-line indices
    rank_indices: list[int] = []
    for idx, line in enumerate(lines):
        if _RANK_LINE.match(line.strip()):
            rank_indices.append(idx)

    results: list[AthleteResult] = []

    for rank_idx in rank_indices:
        rank_line = lines[rank_idx].strip()
        rm = _RANK_LINE.match(rank_line)
        if not rm:
            continue

        rank = int(rm.group(1))
        country = rm.group(2)
        yob = int(rm.group(3))
        total_score = float(rm.group(4))
        pts_str = rm.group(5) or ""
        points_behind = float(pts_str) if pts_str else 0.0

        # The athlete block surrounds the rank line.
        # The entry/name line is always 1 before the rank line and the club line
        # is always 1 after.  Figure score lines extend outward from those anchors
        # by however many standalone figures exist (n_figures - 2, distributed
        # floor(…/2) above the name line and ceil(…/2) below the club line).
        #
        # For n_figures=4: offsets -2, -1, 0, +1, +2
        # For n_figures=3: offsets     -1, 0, +1, +2
        # For n_figures=5: offsets -2, -1, 0, +1, +2, +3
        #
        # Name/entry is always at rank_idx-1; club is always at rank_idx+1.

        name_line = lines[rank_idx - 1].strip() if rank_idx >= 1 else ""
        club_line = lines[rank_idx + 1].strip() if rank_idx + 1 < len(lines) else ""

        # Parse entry number and name from the name line
        entry_number, name = 0, ""
        nm = _ENTRY_NAME.match(name_line)
        if nm:
            entry_number = int(nm.group(1))
            name = nm.group(2).strip()

        # Parse club from the club line
        club = ""
        cm = _CLUB_LINE.match(club_line)
        if cm:
            club = cm.group(1).strip()

        # Build the dynamic athlete block for figure-score scanning.
        # n_figures//2 standalone lines appear before the name line;
        # the remainder appear after the club line.
        lines_above = n_figures // 2
        lines_below = n_figures - n_figures // 2  # includes the club line itself
        block_start = max(0, rank_idx - lines_above)
        block_end = min(len(lines), rank_idx + lines_below + 1)  # +1 for club line
        athlete_block = [lines[i].strip() for i in range(block_start, block_end)]

        # Parse figure scores
        figure_results: list[FigureResult] = []
        for fig_line in athlete_block:
            fsm = _FIG_SCORE.search(fig_line)
            if fsm:
                fig_num = fsm.group(1)
                judge_scores = [float(fsm.group(k)) for k in range(2, 9)]
                score = float(fsm.group(9))
                penalty = float(fsm.group(10))
                figure_results.append(
                    FigureResult(
                        figure_number=fig_num,
                        judge_scores=judge_scores,
                        score=score,
                        penalty=penalty,
                    )
                )

        total_penalty = sum(fr.penalty for fr in figure_results)

        results.append(
            AthleteResult(
                rank=rank,
                entry_number=entry_number,
                name=name,
                club=club,
                country=country,
                yob=yob,
                total_score=total_score,
                penalty=total_penalty,
                points_behind=points_behind,
                figure_results=figure_results,
            )
        )

    return results


def file_sha256(path: Path) -> str:
    """Return the hex SHA-256 digest of the file at *path*."""
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()
