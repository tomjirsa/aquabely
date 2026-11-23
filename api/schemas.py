from pydantic import BaseModel


class CompetitionEntry(BaseModel):
    competition_category_id: int
    competition: str
    date: str | None = None
    age_group_label: str | None = None


class ResultRow(BaseModel):
    rank: int | None = None
    name: str
    year_of_birth: int | None = None
    club: str | None = None
    country: str | None = None
    total_score: float | None = None
    penalty: float | None = None
    points_behind: float | None = None


class FigureRow(BaseModel):
    number: str | None = None
    name: str | None = None
    difficulty: float | None = None


class FigureDetailRow(BaseModel):
    athlete: str
    rank: int | None = None
    figure_name: str | None = None
    coefficient: float | None = None
    judges: list[float | None]
    dropped: list[bool]
    average: float | None = None
    figure_score: float | None = None
    figure_penalty: float | None = None


class HomeSummary(BaseModel):
    level: str
    latest_competition: CompetitionEntry | None = None
    athlete_count: int
    top_scorer_name: str | None = None
    top_scorer_total: float | None = None
