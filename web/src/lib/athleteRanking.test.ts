import { overallOrByYear, rankLabel, rankTone, usesByYearFallback } from "./athleteRanking";

const e = { rank_overall: 2, field_size: 9, rank_by_year: 1, field_size_by_year: 4 } as any;

test("overallOrByYear picks the by-year fields in by-year mode", () => {
  expect(overallOrByYear(e, "by-year")).toEqual({ rank: 1, size: 4 });
});
test("overallOrByYear picks overall fields in overall mode", () => {
  expect(overallOrByYear(e, "overall")).toEqual({ rank: 2, size: 9 });
});
test("by-year mode falls back to overall when by-year rank is null", () => {
  const n = { ...e, rank_by_year: null, field_size_by_year: null };
  expect(overallOrByYear(n, "by-year")).toEqual({ rank: 2, size: 9 });
  expect(usesByYearFallback(n, "by-year")).toBe(true);
  expect(usesByYearFallback(n, "overall")).toBe(false);
  expect(usesByYearFallback(e, "by-year")).toBe(false);
});
test("rankLabel without size shows the rank only", () => {
  expect(rankLabel(3, null)).toBe("3");
});
test("rankLabel with size and null rank", () => {
  expect(rankLabel(3, 9)).toBe("3 / 9");
  expect(rankLabel(null, 9)).toBe("n/a");
});
test("rankTone compares figure rank against overall rank", () => {
  expect(rankTone(1, 3)).toBe("better");
  expect(rankTone(5, 3)).toBe("worse");
  expect(rankTone(3, 3)).toBe("equal");
  expect(rankTone(null, 3)).toBe("none");
});
