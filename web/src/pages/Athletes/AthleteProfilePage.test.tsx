import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";
import { AthleteProfilePage } from "./AthleteProfilePage";
import { apiGet } from "../../api/client";

vi.mock("../../api/client", () => ({ apiGet: vi.fn() }));
const mockGet = vi.mocked(apiGet);
afterEach(() => mockGet.mockReset());

const profile = {
  id: 7, name: "Anna", club: null, year_of_birth: null, competitions: 1, best_score: null, avg_score: null,
  history: [{ level: "L3", competition: "Spring Cup", date: "2025-01-01", age_group: "Open", rank: null, total_score: null, field_size: null }],
  overall_ranks: [{ competition: "Spring Cup", date: "2025-01-01", rank_overall: null, rank_by_year: null, field_size: null, field_size_by_year: null }],
};

test("header and overview render with null values without NaN/undefined", async () => {
  mockGet.mockImplementation(async (path: string) => (path.endsWith("/7") ? profile : []) as any);
  render(
    <MemoryRouter initialEntries={["/athletes/7"]}>
      <Routes><Route path="/athletes/:id" element={<AthleteProfilePage />} /></Routes>
    </MemoryRouter>,
  );
  expect(await screen.findByRole("heading", { name: "Anna" })).toBeInTheDocument();
  expect(screen.getByText("Spring Cup")).toBeInTheDocument();
  expect(document.body.textContent).not.toMatch(/NaN|undefined|null/);
  expect(mockGet).toHaveBeenCalledWith("/api/athletes/7");
  expect(screen.getAllByRole("tab").map((t) => t.textContent)).toEqual(["Overview", "Competitions", "History"]);
  fireEvent.click(screen.getByRole("tab", { name: "Competitions" }));
  expect(mockGet).toHaveBeenCalledWith("/api/athletes/7/competitions");
});
