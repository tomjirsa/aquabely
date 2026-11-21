from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FigureDef:
    number: str
    name: str
    difficulty: float | None
    code: str | None = None


@dataclass(frozen=True)
class FigureResult:
    figure_number: str
    judge_scores: list[float]
    score: float
    penalty: float


@dataclass(frozen=True)
class ParsedResult:
    rank: int
    entry_number: int | None
    name: str
    club: str
    country: str
    year_of_birth: int | None
    total_score: float
    penalty: float
    points_behind: float
    figure_results: list[FigureResult]


@dataclass(frozen=True)
class ParsedCompetition:
    name: str
    date: str
    location: str
    level_code: str
    age_group_label: str
    birth_year_from: int | None
    birth_year_to: int | None
    judges_per_figure: int
    figures: list[FigureDef]
    results: list[ParsedResult]
