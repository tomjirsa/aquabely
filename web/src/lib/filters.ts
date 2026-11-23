import type { ResultRow } from "../api/types";

export interface Filters {
  name: string;
  born: string;
  club: string;
  country: string;
  score: string;
  penalty: string;
  behind: string;
}

export type FilterKey = keyof Filters;

export const EMPTY_FILTERS: Filters = {
  name: "", born: "", club: "", country: "", score: "", penalty: "", behind: "",
};

export interface Range { min: number; max: number }

const N = "(\\d+(?:[.,]\\d+)?)";

export function parseRange(text: string): Range | null {
  const t = text.replace(/\s+/g, "");
  if (!t) return null;
  const toNum = (s: string) => Number(s.replace(",", "."));
  let m = new RegExp(`^${N}$`).exec(t);
  if (m) return { min: toNum(m[1]), max: toNum(m[1]) };
  m = new RegExp(`^${N}-$`).exec(t);
  if (m) return { min: toNum(m[1]), max: Infinity };
  m = new RegExp(`^-${N}$`).exec(t);
  if (m) return { min: -Infinity, max: toNum(m[1]) };
  m = new RegExp(`^${N}-${N}$`).exec(t);
  if (m) return { min: toNum(m[1]), max: toNum(m[2]) };
  return null;
}

function textMatch(value: string | number | null, needle: string): boolean {
  const n = needle.trim().toLowerCase();
  if (!n) return true;
  if (value === null || value === undefined) return false;
  return String(value).toLowerCase().includes(n);
}

function rangeMatch(value: number | null, text: string): boolean {
  const r = parseRange(text);
  if (!r) return true;
  if (value === null || value === undefined) return false;
  return value >= r.min && value <= r.max;
}

export function filterResults(rows: ResultRow[], f: Filters): ResultRow[] {
  return rows.filter(
    (r) =>
      textMatch(r.name, f.name) &&
      textMatch(r.year_of_birth, f.born) &&
      textMatch(r.club, f.club) &&
      textMatch(r.country, f.country) &&
      rangeMatch(r.total_score, f.score) &&
      rangeMatch(r.penalty, f.penalty) &&
      rangeMatch(r.points_behind, f.behind),
  );
}

export function adaptiveRanks(rows: ResultRow[]): { row: ResultRow; position: number }[] {
  return rows.map((row, i) => ({ row, position: i + 1 }));
}

export function isFiltered(f: Filters): boolean {
  return (Object.values(f) as string[]).some((v) => v.trim() !== "");
}
