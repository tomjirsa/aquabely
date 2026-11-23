export type RankMode = "overall" | "by-year";

export interface RankEntry {
  rank_overall: number | null;
  field_size: number | null;
  rank_by_year: number | null;
  field_size_by_year: number | null;
}

/** True when by-year mode was requested but the entry has no by-year rank. */
export function usesByYearFallback(entry: RankEntry, mode: RankMode): boolean {
  return mode === "by-year" && entry.rank_by_year === null;
}

/** Rank and field size for the active mode; by-year falls back to overall when no by-year rank exists. */
export function overallOrByYear(
  entry: RankEntry,
  mode: RankMode,
): { rank: number | null; size: number | null } {
  if (mode === "by-year" && entry.rank_by_year !== null) {
    return { rank: entry.rank_by_year, size: entry.field_size_by_year };
  }
  return { rank: entry.rank_overall, size: entry.field_size };
}

/** "3 / 9", "3" without a field size, "n/a" without a rank. */
export function rankLabel(rank: number | null | undefined, size: number | null | undefined): string {
  if (rank === null || rank === undefined) return "n/a";
  if (size === null || size === undefined) return String(rank);
  return `${rank} / ${size}`;
}

export type RankTone = "better" | "worse" | "equal" | "none";

/** Compares a figure rank with the competition rank (lower is better). */
export function rankTone(
  figureRank: number | null | undefined,
  competitionRank: number | null | undefined,
): RankTone {
  if (figureRank === null || figureRank === undefined) return "none";
  if (competitionRank === null || competitionRank === undefined) return "none";
  if (figureRank < competitionRank) return "better";
  if (figureRank > competitionRank) return "worse";
  return "equal";
}
