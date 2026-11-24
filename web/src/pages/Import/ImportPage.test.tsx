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
  await upload({
    format_id: null, level: null, competition: null, athlete_count: 0,
    errors: ["Could not detect the format: test"],
  });
  const select = screen.getByRole("combobox", { name: /format/i });
  const btn = screen.getByRole("button", { name: "Import" });
  expect(btn).toBeDisabled();
  fireEvent.change(select, { target: { value: "fmt2" } });
  // Choosing a format re-runs the preview; Import enables once it returns.
  await waitFor(() => expect(btn).toBeEnabled());
  expect(screen.getByText("Could not detect the format: test")).toBeInTheDocument();
  expect(document.body.textContent).not.toMatch(/undefined|NaN|null/);
});

test("a real validation error still disables Import after choosing a format", async () => {
  await upload({ format_id: null, errors: ["Could not detect the format: test", "bad row"] });
  fireEvent.change(screen.getByRole("combobox", { name: /format/i }), { target: { value: "fmt2" } });
  await waitFor(() => expect(mockForm).toHaveBeenCalledTimes(2));
  await waitFor(() => expect(screen.getByRole("combobox", { name: /format/i })).toBeEnabled());
  expect(screen.getByRole("button", { name: "Import" })).toBeDisabled();
});

test("400 shows the detail text", async () => {
  await upload();
  mockPost.mockRejectedValue(new ApiError(400, "Parsing failed: boom"));
  fireEvent.click(screen.getByRole("button", { name: "Import" }));
  expect(await screen.findByText("Parsing failed: boom")).toBeInTheDocument();
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

test("format selector is always shown and defaults to the detected format", async () => {
  await upload();
  const select = screen.getByRole("combobox", { name: /format/i });
  expect(select).toHaveValue("fmt1");
});

test("shows the competition name next to level and athlete count", async () => {
  await upload({ competition: "Spring Cup 2026" });
  expect(screen.getByText("Spring Cup 2026")).toBeInTheDocument();
});

test("changing the format re-runs the preview with format_id", async () => {
  await upload();
  const file = (mockForm.mock.calls[0][1] as FormData).get("file");
  mockForm.mockResolvedValue(preview({
    format_id: "fmt2", level: "U12", competition: "Other Cup", athlete_count: 7, errors: ["bad total"],
  }));
  fireEvent.change(screen.getByRole("combobox", { name: /format/i }), { target: { value: "fmt2" } });
  await screen.findByText("Other Cup");
  expect(mockForm).toHaveBeenCalledTimes(2);
  const [path, form] = mockForm.mock.calls[1];
  expect(path).toBe("/api/imports/preview");
  expect((form as FormData).get("format_id")).toBe("fmt2");
  expect((form as FormData).get("file")).toBe(file);
  expect(screen.getByText("U12")).toBeInTheDocument();
  expect(screen.getByText("7")).toBeInTheDocument();
  expect(screen.getByText("bad total")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Import" })).toBeDisabled();
});

test("Import is disabled while the re-preview runs and uses the chosen format", async () => {
  await upload();
  let resolve!: (v: unknown) => void;
  mockForm.mockReturnValue(new Promise((r) => { resolve = r; }) as never);
  fireEvent.change(screen.getByRole("combobox", { name: /format/i }), { target: { value: "fmt2" } });
  expect(screen.getByRole("button", { name: "Import" })).toBeDisabled();
  resolve(preview({ format_id: "fmt2" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Import" })).toBeEnabled());
  mockPost.mockResolvedValue({ athlete_count: 12, level: "L3" });
  fireEvent.click(screen.getByRole("button", { name: "Import" }));
  await screen.findByText("Imported 12 athletes (L3).");
  expect(mockPost).toHaveBeenCalledWith("/api/imports", { sha256: "a".repeat(64), filename: "r.pdf", format_id: "fmt2" });
});
