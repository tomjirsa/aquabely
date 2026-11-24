import { render, screen, within } from "@testing-library/react";
import type { FigureDetailRow, ResultRow } from "../../api/types";
import { FigureDetailTable } from "./FigureDetailTable";
import { ResultsTable } from "./ResultsTable";

const athlete = (rank: number, name = "Anna Novak"): ResultRow => ({
  rank, name, year_of_birth: null, club: null, country: null,
  total_score: null, penalty: null, points_behind: null,
});
const fd = (rank: number, figure: string): FigureDetailRow => ({
  athlete: "Anna Novak", rank, figure_name: figure, coefficient: 1,
  judges: [7, 8], dropped: [false, false], average: 7.5, figure_score: 10, figure_penalty: null,
});

test("same-name athletes only get their own figure rows", () => {
  render(
    <FigureDetailTable
      detail={[fd(1, "Flamingo"), fd(2, "Barracuda")]}
      athletes={[athlete(1), athlete(2)]}
    />,
  );
  const rows = screen.getAllByRole("row").slice(1);
  expect(rows).toHaveLength(2);
  expect(within(rows[0]).getByText("Flamingo")).toBeTruthy();
  expect(within(rows[0]).queryByText("Barracuda")).toBeNull();
  expect(within(rows[1]).getByText("Barracuda")).toBeTruthy();
  expect(within(rows[1]).queryByText("Flamingo")).toBeNull();
});

test("null cells render empty, never dash/NaN/undefined", () => {
  const { container } = render(
    <ResultsTable
      rows={[athlete(1)]}
      filteredRows={[athlete(1)]}
      filters={{} as never}
      onFilterChange={() => {}}
    />,
  );
  const cells = container.querySelectorAll("tbody td");
  const texts = Array.from(cells).map((c) => c.textContent);
  expect(texts.slice(2)).toEqual(["", "", "", "", "", ""]);
  expect(container.textContent).not.toMatch(/NaN|undefined/);
});
