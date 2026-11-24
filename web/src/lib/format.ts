/** Number with fixed decimals; null, undefined and NaN render as an empty cell. */
export function fmtNum(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "";
  return v.toFixed(digits);
}

/** Text or integer value as-is; null and undefined render as an empty cell. */
export function fmtText(v: string | number | null | undefined): string {
  return v === null || v === undefined ? "" : String(v);
}

/** Key used to match figure-detail rows to results (names can repeat). */
export function figureKey(name: string, rank: number | null | undefined): string {
  return `${name}|${rank ?? ""}`;
}
