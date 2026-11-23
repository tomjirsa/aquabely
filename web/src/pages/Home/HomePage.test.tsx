import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { vi } from "vitest";
import { HomePage } from "./HomePage";
import { apiGet } from "../../api/client";

vi.mock("../../api/client", () => ({ apiGet: vi.fn() }));
const mockGet = vi.mocked(apiGet);

const summary = {
  level: "L3",
  latest_competition: { competition_category_id: 1, competition: "Spring Cup", date: "2026-03-01", age_group_label: "2012" },
  athlete_count: 42,
  top_scorer_name: "Jana Novakova",
  top_scorer_total: 87.5,
};

afterEach(() => mockGet.mockReset());

test("shows summary for the selected level", async () => {
  mockGet.mockResolvedValue(summary);
  render(<HomePage />);
  expect(await screen.findByText(/Spring Cup/)).toBeInTheDocument();
  expect(screen.getByText("42")).toBeInTheDocument();
  expect(screen.getByText("Jana Novakova")).toBeInTheDocument();
  expect(screen.getByText("87.50")).toBeInTheDocument();
  expect(mockGet).toHaveBeenCalledWith("/api/home?level=L3");
});

test("level switch reloads with U12", async () => {
  mockGet.mockResolvedValue(summary);
  render(<HomePage />);
  await screen.findByText(/Spring Cup/);
  fireEvent.click(screen.getByRole("button", { name: "U12" }));
  expect(screen.getByRole("button", { name: "U12" })).toHaveAttribute("aria-pressed", "true");
  await waitFor(() => expect(mockGet).toHaveBeenCalledWith("/api/home?level=U12"));
});

test("empty state when no competition", async () => {
  mockGet.mockResolvedValue({ ...summary, latest_competition: null, athlete_count: 0, top_scorer_name: null, top_scorer_total: null });
  render(<HomePage />);
  expect(await screen.findByText("No L3 competitions yet. Use the Import page to add one.")).toBeInTheDocument();
});
