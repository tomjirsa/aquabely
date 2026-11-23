import { fireEvent, render, screen, within } from "@testing-library/react";

import { vi } from "vitest";
import { FiguresPage } from "./FiguresPage";
import { apiGet } from "../../api/client";

vi.mock("../../api/client", () => ({ apiGet: vi.fn() }));
const mockGet = vi.mocked(apiGet);

afterEach(() => mockGet.mockReset());

test("renders catalogue table headers and rows", async () => {
  mockGet.mockResolvedValue([
    { code: "101", name: "Ballet leg", coefficient: 1.6, description_cs: "Popis", performances: 12, competitions: "Spring Cup" },
    { code: null, name: null, coefficient: null, description_cs: null, performances: 0, competitions: null },
  ]);
  render(<FiguresPage />);
  expect(await screen.findByText("Ballet leg")).toBeInTheDocument();
  const headers = screen.getAllByRole("columnheader").map((h) => h.textContent);
  expect(headers).toEqual(["Code", "Name", "Coefficient", "Description", "Performances", "Competitions"]);
  expect(screen.getByText("1.60")).toBeInTheDocument();
  expect(mockGet).toHaveBeenCalledWith("/api/figures?level=L3");
});

test("level switch requests U12", async () => {
  mockGet.mockResolvedValue([]);
  render(<FiguresPage />);
  await screen.findByText("No figures in the catalogue for this level.");
  fireEvent.click(screen.getByRole("button", { name: "U12" }));
  await within(document.body).findByText("No figures in the catalogue for this level.");
  expect(mockGet).toHaveBeenCalledWith("/api/figures?level=U12");
});
