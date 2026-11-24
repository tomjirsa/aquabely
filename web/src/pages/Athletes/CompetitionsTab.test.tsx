import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { CompetitionsTab } from "./CompetitionsTab";
import { apiGet } from "../../api/client";

vi.mock("../../api/client", () => ({ apiGet: vi.fn() }));
const mockGet = vi.mocked(apiGet);
afterEach(() => mockGet.mockReset());

const fig = {
  figure_name: "Ballet leg", coefficient: 1.6, fig_rank_overall: 1, fig_rank_by_year: 2,
  fig_field_size: 9, fig_field_size_by_year: 4,
  judges: [7, 6.5, 8, null], dropped: [false, true, false, false], average: 7.5, figure_score: 12,
};
const comps = [
  { date: "2025-01-01", competition: "Empty Cup", rank_overall: 2, rank_by_year: 1, field_size: 9, field_size_by_year: 4, figures: [] },
  { date: "2025-02-01", competition: "Full Cup", rank_overall: 3, rank_by_year: null, field_size: 8, field_size_by_year: null, figures: [fig] },
];

test("competition without figures shows the empty message and overall rank", async () => {
  mockGet.mockResolvedValue([comps[0]]);
  render(<CompetitionsTab athleteId={7} />);
  expect(await screen.findByText("No figure results for this competition.")).toBeInTheDocument();
  expect(screen.getByText("Rank overall: 2 / 9")).toBeInTheDocument();
  expect(mockGet).toHaveBeenCalledWith("/api/athletes/7/competitions");
});

test("by-year mode shows by-year rank, and falls back with a note when null", async () => {
  mockGet.mockResolvedValue(comps);
  render(<CompetitionsTab athleteId={7} />);
  await screen.findByText("Rank overall: 2 / 9");
  fireEvent.click(screen.getByRole("button", { name: "By year" }));
  expect(screen.getByRole("button", { name: "By year" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByText("Rank by year: 1 / 4")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("tab", { name: "Full Cup" }));
  expect(screen.getByText("Rank overall: 3 / 8")).toBeInTheDocument();
  expect(screen.getByText("Overall (no by-year rank)")).toBeInTheDocument();
  expect(screen.getByText("7.0")).toBeInTheDocument();
  expect(screen.getByText("6.5").tagName).toBe("S");
  expect(document.body.textContent).not.toMatch(/NaN|undefined|null/);
});
