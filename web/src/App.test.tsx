import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { App } from "./App";

test("nav lists the five main pages in order", () => {
  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
  const links = screen.getAllByRole("link").map((a) => a.textContent);
  expect(links.slice(0, 5)).toEqual(["Home", "Competitions", "Figures", "Athletes", "Clubs"]);
});
