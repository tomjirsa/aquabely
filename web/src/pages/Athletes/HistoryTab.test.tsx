import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { HistoryTab } from "./HistoryTab";
import { apiGet } from "../../api/client";

vi.mock("../../api/client", () => ({ apiGet: vi.fn() }));
const mockGet = vi.mocked(apiGet);
afterEach(() => mockGet.mockReset());

test("one sub-tab per figure and endpoint called", async () => {
  mockGet.mockResolvedValue([
    { figure_name: "Ballet leg", points: [] },
    { figure_name: "Barracuda", points: [] },
  ]);
  render(<HistoryTab athleteId={7} />);
  expect(await screen.findByRole("tab", { name: "Ballet leg" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("tab", { name: "Barracuda" }));
  expect(screen.getByRole("tab", { name: "Barracuda" })).toHaveAttribute("aria-selected", "true");
  expect(mockGet).toHaveBeenCalledWith("/api/athletes/7/figures");
});

test("no figures shows an empty message", async () => {
  mockGet.mockResolvedValue([]);
  render(<HistoryTab athleteId={7} />);
  expect(await screen.findByText("No figure history for this athlete.")).toBeInTheDocument();
});
