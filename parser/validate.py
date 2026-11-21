from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean

from parser.models import ParsedCompetition

SCORE_TOLERANCE = 0.01


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate(comp: ParsedCompetition) -> ValidationReport:
    rep = ValidationReport()
    difficulty = {f.number: f.difficulty for f in comp.figures}

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
                expected = mean(fr.judge_scores) * d
                if abs(fr.score - expected) > SCORE_TOLERANCE:
                    rep.warnings.append(
                        f"{r.name} {fr.figure_number}: score {fr.score} differs from "
                        f"mean(judges) x difficulty = {expected:.3f}")

    for a in comp.results:
        for b in comp.results:
            if a.total_score > b.total_score and a.rank > b.rank:
                rep.errors.append(
                    f"Rank inconsistent: {a.name} (rank {a.rank}, {a.total_score}) "
                    f"outscores {b.name} (rank {b.rank}, {b.total_score})")
    return rep
