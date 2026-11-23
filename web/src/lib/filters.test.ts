import { adaptiveRanks, filterResults, isFiltered, parseRange, type Filters } from "./filters";
import type { ResultRow } from "../api/types";

const empty: Filters = { name: "", born: "", club: "", country: "", score: "", penalty: "", behind: "" };

function row(over: Partial<ResultRow>): ResultRow {
  return {
    rank: 1, name: "A", year_of_birth: 2010, club: "Club", country: "CZE",
    total_score: 50, penalty: 0, points_behind: 0, ...over,
  };
}

test.each([
  ["10-20", { min: 10, max: 20 }],
  ["10-", { min: 10, max: Infinity }],
  ["-5", { min: -Infinity, max: 5 }],
  ["10", { min: 10, max: 10 }],
  ["", null],
  ["abc", null],
])("parseRange(%s)", (input, expected) => {
  expect(parseRange(input)).toEqual(expected);
});

test("adaptiveRanks renumbers over filtered rows", () => {
  const rows = [{ rank: 1 }, { rank: 3 }, { rank: 4 }] as ResultRow[];
  expect(adaptiveRanks(rows.slice(1)).map((x) => x.position)).toEqual([1, 2]);
});

test("filterResults drops rows with null score for a range filter", () => {
  const rows = [row({ name: "A", total_score: null }), row({ name: "B", total_score: 55 })];
  expect(filterResults(rows, { ...empty, score: "50-60" }).map((r) => r.name)).toEqual(["B"]);
  expect(filterResults(rows, empty).map((r) => r.name)).toEqual(["A", "B"]);
  expect(filterResults(rows, { ...empty, score: "  " }).map((r) => r.name)).toEqual(["A", "B"]);
});

test("filterResults matches text case-insensitively and combines filters", () => {
  const rows = [
    row({ name: "Eva", club: "Slavia Praha" }),
    row({ name: "Jan", club: "Sparta Praha", year_of_birth: 2011 }),
    row({ name: "Ota", club: "Brno" }),
    row({ name: "Nul", club: null }),
  ];
  expect(filterResults(rows, { ...empty, club: "praha" }).map((r) => r.name)).toEqual(["Eva", "Jan"]);
  expect(filterResults(rows, { ...empty, club: "praha", born: "2011" }).map((r) => r.name)).toEqual(["Jan"]);
});

test("isFiltered", () => {
  expect(isFiltered(empty)).toBe(false);
  expect(isFiltered({ ...empty, club: " " })).toBe(false);
  expect(isFiltered({ ...empty, club: "x" })).toBe(true);
});
