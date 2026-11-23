// Mirrors api/schemas.py (snake_case, nullable where the backend allows null).

export interface CompetitionEntry {
  competition_category_id: number;
  competition: string;
  date: string | null;
  age_group_label: string | null;
}
/** Brief name for CompetitionEntry. */
export type Competition = CompetitionEntry;

export interface ResultRow {
  rank: number | null;
  name: string;
  year_of_birth: number | null;
  club: string | null;
  country: string | null;
  total_score: number | null;
  penalty: number | null;
  points_behind: number | null;
}

export interface FigureRow {
  number: string | null;
  name: string | null;
  difficulty: number | null;
}

export interface FigureDetailRow {
  athlete: string;
  rank: number | null;
  figure_name: string | null;
  coefficient: number | null;
  judges: (number | null)[];
  dropped: boolean[];
  average: number | null;
  figure_score: number | null;
  figure_penalty: number | null;
}

export interface HomeSummary {
  level: string;
  latest_competition: CompetitionEntry | null;
  athlete_count: number;
  top_scorer_name: string | null;
  top_scorer_total: number | null;
}

export interface AthleteSummary {
  id: number;
  name: string;
  club: string | null;
  year_of_birth: number | null;
  competitions: number;
  best_score: number | null;
  avg_score: number | null;
}

export interface AthleteHistoryRow {
  level: string | null;
  competition: string;
  date: string | null;
  age_group: string | null;
  rank: number | null;
  total_score: number | null;
  field_size: number | null;
}

export interface OverallRank {
  competition: string;
  date: string | null;
  rank_overall: number | null;
  rank_by_year: number | null;
  field_size: number | null;
  field_size_by_year: number | null;
}

export interface AthleteProfile extends AthleteSummary {
  history: AthleteHistoryRow[];
  overall_ranks: OverallRank[];
}

export interface AthleteFigure {
  figure_name: string | null;
  coefficient: number | null;
  fig_rank_overall: number | null;
  fig_rank_by_year: number | null;
  fig_field_size: number | null;
  fig_field_size_by_year: number | null;
  judges: (number | null)[];
  dropped: boolean[];
  average: number | null;
  figure_score: number | null;
}

export interface AthleteCompetition {
  date: string | null;
  competition: string;
  rank_overall: number | null;
  rank_by_year: number | null;
  field_size: number | null;
  field_size_by_year: number | null;
  figures: AthleteFigure[];
}

export interface FigurePoint {
  date: string | null;
  competition: string;
  judges: (number | null)[];
  dropped: boolean[];
  average: number | null;
  figure_score: number | null;
}

export interface FigureHistory {
  figure_name: string | null;
  points: FigurePoint[];
}

export interface CatalogueFigure {
  code: string | null;
  name: string | null;
  coefficient: number | null;
  description_cs: string | null;
  performances: number;
  competitions: string | null;
}

export interface ClubSummary {
  id: number;
  name: string;
}

export interface RosterEntry {
  name: string;
  year_of_birth: number | null;
  country: string | null;
}

export interface MedalCount {
  place: number;
  count: number;
}

export interface ClubAvgScore {
  competition: string;
  date: string | null;
  avg_total: number | null;
}

export interface ClubDetail {
  name: string;
  roster: RosterEntry[];
  medals: MedalCount[];
  avg_scores: ClubAvgScore[];
}

export interface ImportPreview {
  sha256: string;
  filename: string;
  format_id: string | null;
  available_formats: string[];
  level: string | null;
  competition: string | null;
  athlete_count: number;
  errors: string[];
  warnings: string[];
}

export interface ImportRequest {
  sha256: string;
  filename: string;
  format_id: string;
}

export interface ImportResult {
  athlete_count: number;
  level: string | null;
}
