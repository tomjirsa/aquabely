from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean

from parser.figure_match import UnmatchedFigureError, match_figure
from parser.models import ParsedCompetition

SCORE_TOLERANCE = 0.05


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate(comp: ParsedCompetition) -> ValidationReport:
    rep = ValidationReport()
    difficulty: dict[str, float] = {}
    names = {f.number: f.name for f in comp.figures}
    for f in comp.figures:
        try:
            difficulty[f.number] = match_figure(comp.level_code, f.name, f.code).coefficient
        except UnmatchedFigureError:
            rep.errors.append(f"unknown figure: {f.name}")

    for r in comp.results:
        if len(r.figure_results) != len(comp.figures):
            rep.errors.append(
                f"{r.name}: {len(r.figure_results)} figure results, expected {len(comp.figures)} figures")
        for fr in r.figure_results:
            if len(fr.judge_scores) != comp.judges_per_figure:
                rep.errors.append(
                    f"{r.name} {fr.figure_number}: {len(fr.judge_scores)} judge scores, "
                    f"expected {comp.judges_per_figure}")
                continue
            d = difficulty.get(fr.figure_number)
            if d is not None and fr.judge_scores:
                trimmed = sorted(fr.judge_scores)[1:-1]
                expected = mean(trimmed) * d if trimmed else 0.0
                if abs(fr.score - expected) > SCORE_TOLERANCE:
                    rep.warnings.append(
                        f"{r.name} {fr.figure_number} ({names.get(fr.figure_number)}): score {fr.score} differs from "
                        f"trimmed mean(judges) x difficulty = {expected:.3f}")

    for a in comp.results:
        for b in comp.results:
            if a.total_score > b.total_score and a.rank > b.rank:
                rep.errors.append(
                    f"Rank inconsistent: {a.name} (rank {a.rank}, {a.total_score}) "
                    f"outscores {b.name} (rank {b.rank}, {b.total_score})")
    return rep
