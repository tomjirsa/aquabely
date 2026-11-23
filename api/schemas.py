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


class AthleteSummary(BaseModel):
    id: int
    name: str
    club: str | None = None
    year_of_birth: int | None = None
    competitions: int
    best_score: float | None = None
    avg_score: float | None = None


class AthleteHistoryRow(BaseModel):
    level: str | None = None
    competition: str
    date: str | None = None
    age_group: str | None = None
    rank: int | None = None
    total_score: float | None = None
    field_size: int | None = None


class OverallRank(BaseModel):
    competition: str
    date: str | None = None
    rank_overall: int | None = None
    rank_by_year: int | None = None
    field_size: int | None = None
    field_size_by_year: int | None = None


class AthleteProfile(AthleteSummary):
    history: list[AthleteHistoryRow]
    overall_ranks: list[OverallRank]


class AthleteFigure(BaseModel):
    figure_name: str | None = None
    coefficient: float | None = None
    fig_rank_overall: int | None = None
    fig_rank_by_year: int | None = None
    fig_field_size: int | None = None
    fig_field_size_by_year: int | None = None
    judges: list[float | None]
    dropped: list[bool]
    average: float | None = None
    figure_score: float | None = None


class AthleteCompetition(BaseModel):
    date: str | None = None
    competition: str
    rank_overall: int | None = None
    rank_by_year: int | None = None
    field_size: int | None = None
    field_size_by_year: int | None = None
    figures: list[AthleteFigure]


class FigurePoint(BaseModel):
    date: str | None = None
    competition: str
    judges: list[float | None]
    dropped: list[bool]
    average: float | None = None
    figure_score: float | None = None


class FigureHistory(BaseModel):
    figure_name: str | None = None
    points: list[FigurePoint]


class CatalogueFigure(BaseModel):
    code: str | None = None
    name: str | None = None
    coefficient: float | None = None
    description_cs: str | None = None
    performances: int
    competitions: str | None = None


class ClubSummary(BaseModel):
    id: int
    name: str


class RosterEntry(BaseModel):
    name: str
    year_of_birth: int | None = None
    country: str | None = None


class MedalCount(BaseModel):
    place: int
    count: int


class ClubAvgScore(BaseModel):
    competition: str
    date: str | None = None
    avg_total: float | None = None


class ClubDetail(BaseModel):
    name: str
    roster: list[RosterEntry]
    medals: list[MedalCount]
    avg_scores: list[ClubAvgScore]
