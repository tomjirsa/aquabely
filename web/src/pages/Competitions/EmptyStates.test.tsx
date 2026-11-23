import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import type { FigureDetailRow, ResultRow } from "../../api/types";
import { EMPTY_FILTERS } from "../../lib/filters";
import { apiGet } from "../../api/client";
import { CompetitionsPage } from "./CompetitionsPage";
import { FigureDetailTable } from "./FigureDetailTable";
import { ResultsTable } from "./ResultsTable";

vi.mock("../../api/client", () => ({ apiGet: vi.fn() }));
const mockGet = vi.mocked(apiGet);
afterEach(() => mockGet.mockReset());

const athlete = (rank: number, name = "Anna Novak"): ResultRow => ({
  rank, name, year_of_birth: null, club: null, country: null,
  total_score: null, penalty: null, points_behind: null,
});
const fd = (rank: number, athleteName: string): FigureDetailRow => ({
  athlete: athleteName, rank, figure_name: "Flamingo", coefficient: 1,
  judges: [7, 8], dropped: [false, false], average: 7.5, figure_score: 10, figure_penalty: null,
});

test("results table shows a message when filters match no rows", () => {
  const { container } = render(
    <ResultsTable
      rows={[athlete(1)]}
      filteredRows={[]}
      filters={{ ...EMPTY_FILTERS, name: "zzz" }}
      onFilterChange={() => {}}
    />,
  );
  expect(screen.getByText("No results match these filters.")).toBeInTheDocument();
  // The filter row stays so the user can clear the filters; the body is never empty.
  expect(container.querySelectorAll("tbody tr")).toHaveLength(1);
});

test("results table shows a message when the competition has no results", () => {
  const { container } = render(
    <ResultsTable rows={[]} filteredRows={[]} filters={EMPTY_FILTERS} onFilterChange={() => {}} />,
  );
  expect(screen.getByText("No results for this competition.")).toBeInTheDocument();
  expect(container.querySelector("tbody")).toBeNull();
});

test("figure detail shows a message when shown athletes have no figure results", () => {
  const { container } = render(
    <FigureDetailTable detail={[fd(5, "Someone Else")]} athletes={[athlete(1)]} />,
  );
  expect(screen.getByText("No figure results for these athletes.")).toBeInTheDocument();
  expect(container.querySelector("tbody")).toBeNull();
});

test("figure detail shows a message when no athletes are shown", () => {
  render(<FigureDetailTable detail={[]} athletes={[]} />);
  expect(screen.getByText("No figure results for these athletes.")).toBeInTheDocument();
});

test("a level with no competitions points to the Import page", async () => {
  mockGet.mockResolvedValue([]);
  render(<CompetitionsPage />);
  expect(
    await screen.findByText("No L3 competitions yet. Use the Import page to add one."),
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "U12" }));
  expect(
    await screen.findByText("No U12 competitions yet. Use the Import page to add one."),
  ).toBeInTheDocument();
});

test("a competition with no results shows one message and no tables", async () => {
  mockGet.mockImplementation((path: string) => {
    if (path.startsWith("/api/competitions?")) {
      return Promise.resolve([{ competition_category_id: 7, competition: "Cup", age_group_label: null, date: null }]);
    }
    return Promise.resolve([]);
  });
  const { container } = render(<CompetitionsPage />);
  await screen.findByRole("option", { name: "Cup" });
  fireEvent.change(screen.getByLabelText("Competition"), { target: { value: "7" } });
  expect(await screen.findByText("No results for this competition.")).toBeInTheDocument();
  await waitFor(() => expect(mockGet).toHaveBeenCalledWith("/api/competitions/7/figure-detail"));
  expect(container.querySelector("table")).toBeNull();
  expect(screen.queryByText("No figure results for these athletes.")).toBeNull();
});
