import { fmtNum, fmtText, figureKey } from "./format";

test("fmtNum renders null and undefined as empty, 0 as 0.00", () => {
  expect(fmtNum(null)).toBe("");
  expect(fmtNum(undefined)).toBe("");
  expect(fmtNum(0)).toBe("0.00");
  expect(fmtNum(12.345)).toBe("12.35");
  expect(fmtNum(Number.NaN)).toBe("");
});

test("fmtText renders null and undefined as empty", () => {
  expect(fmtText(null)).toBe("");
  expect(fmtText(undefined)).toBe("");
  expect(fmtText(2008)).toBe("2008");
  expect(fmtText("CZE")).toBe("CZE");
});

test("figureKey combines name and rank", () => {
  expect(figureKey("Anna", 1)).toBe("Anna|1");
  expect(figureKey("Anna", null)).toBe("Anna|");
});

test("fmtNum with one decimal renders judge marks like 7.0", () => {
  expect(fmtNum(7, 1)).toBe("7.0");
  expect(fmtNum(7.25, 1)).toBe("7.3");
  expect(fmtNum(null, 1)).toBe("");
});
