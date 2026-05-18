from dataclasses import dataclass, field


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
