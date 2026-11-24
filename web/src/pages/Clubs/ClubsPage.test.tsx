import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { ClubsPage } from "./ClubsPage";
import { apiGet } from "../../api/client";

vi.mock("../../api/client", () => ({ apiGet: vi.fn() }));
const mockGet = vi.mocked(apiGet);
afterEach(() => mockGet.mockReset());

test("lists clubs as links to the detail page", async () => {
  mockGet.mockResolvedValue([{ id: 4, name: "Aqua" }, { id: 5, name: "Delfin" }]);
  render(<MemoryRouter><ClubsPage /></MemoryRouter>);
  const link = await screen.findByRole("link", { name: "Aqua" });
  expect(link).toHaveAttribute("href", "/clubs/4");
  expect(mockGet).toHaveBeenCalledWith("/api/clubs");
});

test("shows empty state and errors", async () => {
  mockGet.mockResolvedValue([]);
  render(<MemoryRouter><ClubsPage /></MemoryRouter>);
  expect(await screen.findByText("No clubs found.")).toBeInTheDocument();
});
