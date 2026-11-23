import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { ImportPage } from "./ImportPage";
import { apiPost, apiPostForm, ApiError } from "../../api/client";

vi.mock("../../api/client", async (orig) => ({
  ...(await orig<typeof import("../../api/client")>()),
  apiPost: vi.fn(),
  apiPostForm: vi.fn(),
}));
const mockPost = vi.mocked(apiPost);
const mockForm = vi.mocked(apiPostForm);
afterEach(() => { mockPost.mockReset(); mockForm.mockReset(); });

const preview = (over: object = {}) => ({
  sha256: "a".repeat(64), filename: "r.pdf", format_id: "fmt1",
  available_formats: ["fmt1", "fmt2"], level: "L3", competition: "Cup",
  athlete_count: 12, errors: [], warnings: [], ...over,
});

async function upload(over: object = {}, file = new File(["x"], "r.pdf", { type: "application/pdf" })) {
  mockForm.mockResolvedValue(preview(over));
  render(<ImportPage />);
  fireEvent.change(screen.getByLabelText(/choose pdf/i), { target: { files: [file] } });
  await screen.findByText("r.pdf");
}

test("errors disable Import", async () => {
  await upload({ errors: ["x"] });
  expect(screen.getByText("x")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Import" })).toBeDisabled();
});

test("undetected format shows dropdown and Import is disabled until chosen", async () => {
  await upload({ format_id: null, level: null, competition: null, athlete_count: 0 });
  const select = screen.getByRole("combobox", { name: /format/i });
  const btn = screen.getByRole("button", { name: "Import" });
  expect(btn).toBeDisabled();
  fireEvent.change(select, { target: { value: "fmt2" } });
  expect(btn).toBeEnabled();
  expect(document.body.textContent).not.toMatch(/undefined|NaN|null/);
});

test("shows level, count and collapsible warnings", async () => {
  await upload({ warnings: ["w1"] });
  expect(screen.getByText(/L3/)).toBeInTheDocument();
  expect(screen.getByText(/12/)).toBeInTheDocument();
  expect(screen.getByText("w1").closest("details")).not.toBeNull();
});

test("successful import shows message and posts body", async () => {
  await upload();
  mockPost.mockResolvedValue({ athlete_count: 12, level: "L3" });
  fireEvent.click(screen.getByRole("button", { name: "Import" }));
  expect(await screen.findByText("Imported 12 athletes (L3).")).toBeInTheDocument();
  expect(mockPost).toHaveBeenCalledWith("/api/imports", { sha256: "a".repeat(64), filename: "r.pdf", format_id: "fmt1" });
});

test("409 shows Already imported.", async () => {
  await upload();
  mockPost.mockRejectedValue(new ApiError(409, "Already imported"));
  fireEvent.click(screen.getByRole("button", { name: "Import" }));
  expect(await screen.findByText("Already imported.")).toBeInTheDocument();
});

test("422 shows validation errors text", async () => {
  await upload();
  mockPost.mockRejectedValue(new ApiError(422, "Validation failed", { detail: "Validation failed", errors: ["bad row", "bad col"] }));
  fireEvent.click(screen.getByRole("button", { name: "Import" }));
  expect(await screen.findByText(/bad row; bad col/)).toBeInTheDocument();
});

test("404 and 400 show the detail text", async () => {
  await upload();
  mockPost.mockRejectedValue(new ApiError(404, "Upload not found"));
  fireEvent.click(screen.getByRole("button", { name: "Import" }));
  expect(await screen.findByText("Upload not found")).toBeInTheDocument();
});

test("oversized file is rejected before upload", async () => {
  render(<ImportPage />);
  const big = new File(["x"], "big.pdf", { type: "application/pdf" });
  Object.defineProperty(big, "size", { value: 50 * 1024 * 1024 + 1 });
  fireEvent.change(screen.getByLabelText(/choose pdf/i), { target: { files: [big] } });
  expect(await screen.findByText("File exceeds 50 MB")).toBeInTheDocument();
  expect(mockForm).not.toHaveBeenCalled();
});

test("preview failure (413) shows the error", async () => {
  mockForm.mockRejectedValue(new ApiError(413, "File exceeds 50 MB"));
  render(<ImportPage />);
  fireEvent.change(screen.getByLabelText(/choose pdf/i), { target: { files: [new File(["x"], "r.pdf")] } });
  await waitFor(() => expect(screen.getByText("File exceeds 50 MB")).toBeInTheDocument());
});
