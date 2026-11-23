import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";
import { AthletesPage } from "./AthletesPage";
import { apiGet } from "../../api/client";

vi.mock("../../api/client", () => ({ apiGet: vi.fn() }));
const mockGet = vi.mocked(apiGet);
afterEach(() => mockGet.mockReset());

const rows = [
  { id: 7, name: "Anna", club: "Aqua", year_of_birth: 2008, competitions: 3, best_score: 80.5, avg_score: 70 },
  { id: 8, name: "Bara", club: null, year_of_birth: null, competitions: 0, best_score: null, avg_score: null },
];

test("lists athletes, shows empty cells for nulls, and navigates on row click", async () => {
  mockGet.mockResolvedValue(rows);
  render(
    <MemoryRouter initialEntries={["/athletes"]}>
      <Routes>
        <Route path="/athletes" element={<AthletesPage />} />
        <Route path="/athletes/:id" element={<h1>profile page</h1>} />
      </Routes>
    </MemoryRouter>,
  );
  expect(await screen.findByText("Anna")).toBeInTheDocument();
  expect(screen.getAllByRole("columnheader").map((h) => h.textContent)).toEqual(
    ["Athlete", "Club", "Competitions", "Best score"]);
  expect(screen.getByText("80.50")).toBeInTheDocument();
  expect(document.body.textContent).not.toMatch(/NaN|undefined|null/);
  expect(mockGet).toHaveBeenCalledWith("/api/athletes?q=");
  fireEvent.click(screen.getByText("Anna"));
  expect(await screen.findByText("profile page")).toBeInTheDocument();
});

test("search box requests with q", async () => {
  mockGet.mockResolvedValue([]);
  render(<MemoryRouter><AthletesPage /></MemoryRouter>);
  fireEvent.change(screen.getByRole("searchbox"), { target: { value: "aq" } });
  await screen.findByText("No athletes found.");
  await vi.waitFor(() => expect(mockGet).toHaveBeenCalledWith("/api/athletes?q=aq"));
});
