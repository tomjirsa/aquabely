import { afterEach, expect, test, vi } from "vitest";
import { apiGet, apiPostForm, ApiError } from "./client";

afterEach(() => vi.restoreAllMocks());

test("apiGet throws ApiError with status on 404", async () => {
  globalThis.fetch = vi.fn(async () => new Response("{}", { status: 404 })) as any;
  await expect(apiGet("/api/nope")).rejects.toMatchObject({ status: 404 });
});

test("apiGet returns parsed JSON on 200", async () => {
  globalThis.fetch = vi.fn(async () => new Response(JSON.stringify({ a: 1 }), { status: 200 })) as any;
  await expect(apiGet<{ a: number }>("/api/x")).resolves.toEqual({ a: 1 });
});

test("ApiError uses backend detail as message", async () => {
  globalThis.fetch = vi.fn(async () => new Response(JSON.stringify({ detail: "bad" }), { status: 422 })) as any;
  const err: ApiError = await apiGet<unknown>("/api/x").then(() => { throw new Error("no throw"); }).catch((e: unknown) => e as ApiError);
  expect(err).toBeInstanceOf(ApiError);
  expect(err.message).toBe("bad");
  expect(err.status).toBe(422);
});

test("apiPostForm posts FormData", async () => {
  const f = vi.fn(async () => new Response("{}", { status: 201 }));
  globalThis.fetch = f as any;
  const fd = new FormData();
  await apiPostForm("/api/import", fd);
  expect(f).toHaveBeenCalledWith("/api/import", { method: "POST", body: fd });
});
