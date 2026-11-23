import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";
import { ClubDetailPage } from "./ClubDetailPage";
import { apiGet } from "../../api/client";

vi.mock("../../api/client", () => ({ apiGet: vi.fn() }));
const mockGet = vi.mocked(apiGet);
afterEach(() => mockGet.mockReset());

function renderAt(id: string) {
  return render(
    <MemoryRouter initialEntries={[`/clubs/${id}`]}>
      <Routes><Route path="/clubs/:id" element={<ClubDetailPage />} /></Routes>
    </MemoryRouter>,
  );
}

const detail = {
  name: "Aqua Club",
  roster: [
    { name: "Anna", year_of_birth: 2008, country: "CZE" },
    { name: "Bara", year_of_birth: null, country: null },
  ],
  medals: [{ place: 2, count: 2 }, { place: 1, count: 5 }],
  avg_scores: [{ competition: "Cup", date: "2024-05-01", avg_total: 71.456 }],
};

test("renders heading, roster rows and medal counts", async () => {
  mockGet.mockResolvedValue(detail);
  renderAt("3");
  expect(await screen.findByRole("heading", { name: "Aqua Club" })).toBeInTheDocument();
  expect(mockGet).toHaveBeenCalledWith("/api/clubs/3");
  expect(screen.getByText("Anna")).toBeInTheDocument();
  expect(screen.getByText("2008")).toBeInTheDocument();
  expect(screen.getByText("Bara")).toBeInTheDocument();
  expect(within(screen.getByTestId("medal-2")).getByText("2")).toBeInTheDocument();
  expect(within(screen.getByTestId("medal-1")).getByText("5")).toBeInTheDocument();
  expect(within(screen.getByTestId("medal-3")).getByText("0")).toBeInTheDocument();
  expect(document.body.textContent).not.toMatch(/NaN|undefined|null/);
});

test("unknown club shows an error message", async () => {
  mockGet.mockRejectedValue(new Error("Club not found"));
  renderAt("999");
  expect(await screen.findByRole("alert")).toHaveTextContent("Club not found");
});
